"""Root pytest configuration and shared factories.

The platform tests share four core data shapes — :class:`User`,
:class:`Company`, :class:`Branch`, and :class:`CompanyMembership`. This
conftest exposes ``make_*`` factory fixtures so individual tests can express
what they need without re-implementing the same setup block.

Usage::

    def test_owner_can_invite(make_user, make_company, make_membership):
        owner = make_user(login_id="alice")
        company = make_company(owner=owner)
        membership = make_membership(user=owner, company=company, role="owner")
        ...

The factories accept keyword overrides and use deterministic defaults that
match the "happy path" used in existing tests (``login_id="..."``,
``code="testco"``, ``status="active"``, ``trial_ends_at`` in 2030).

For session-aware HTTP tests, see :func:`force_login_company` which combines
:class:`Client` creation, ``force_login``, and the company session middleware
key in one call.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, time
from typing import Any
from uuid import uuid4

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

import django

django.setup()

import pytest  # noqa: E402
from django.test import Client  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.identity.models import User  # noqa: E402
from apps.organizations.models import Branch, CompanyMembership, CompanyRole, JobRole, UserBranchMembership  # noqa: E402
from apps.tenancy.models import Company, CompanyStatus  # noqa: E402
from apps.tasks.models import (  # noqa: E402
    TaskAssignmentMode,
    TaskInstance,
    TaskRecurrenceType,
    TaskSchedule,
    TaskTemplate,
    TaskTemplateVersion,
)
from apps.evidence.models import CaptureSession, EvidenceItem, EvidenceType  # noqa: E402

# ---------------------------------------------------------------------------
# Counters (module-level so each test invocation increments independently).
# ---------------------------------------------------------------------------
_user_counter = {"n": 0}
_company_counter = {"n": 0}
_branch_counter = {"n": 0}


def _next_user_login(prefix: str = "user") -> str:
    _user_counter["n"] += 1
    return f"{prefix}-{_user_counter['n']}"


def _next_company_code(prefix: str = "co") -> str:
    _company_counter["n"] += 1
    return f"{prefix}-{_company_counter['n']}"


def _next_branch_code(prefix: str = "branch") -> str:
    _branch_counter["n"] += 1
    return f"{prefix}-{_branch_counter['n']}"


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


@pytest.fixture
def make_user(db) -> Callable[..., User]:
    """Return a factory that creates a :class:`User`."""

    def _factory(*, login_id: str | None = None, password: str = "TestPass123!", **kwargs: Any) -> User:
        return User.objects.create_user(
            login_id=login_id or _next_user_login(),
            password=password,
            display_name=kwargs.pop("display_name", None) or "Test User",
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_company(db, make_user) -> Callable[..., Company]:
    """Return a factory that creates a :class:`Company`.

    The factory auto-creates an owner user unless ``owner`` is provided. The
    default ``trial_ends_at`` matches the 2030 sentinel used throughout the
    existing tests so the company is "operational" without further changes.
    """

    def _factory(
        *,
        code: str | None = None,
        status: str = CompanyStatus.ACTIVE,
        owner: User | None = None,
        industry: str = "other",
        trial_ends_at: datetime | None = None,
        **kwargs: Any,
    ) -> Company:
        owner = owner or make_user(login_id=_next_user_login(prefix="owner"))
        return Company.objects.create(
            name=kwargs.pop("name", f"Test Company {uuid4().hex[:6]}"),
            code=code or _next_company_code(),
            industry=industry,
            owner=owner,
            status=status,
            trial_ends_at=trial_ends_at or timezone.make_aware(datetime(2030, 1, 1, 0, 0)),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_branch(db, make_company) -> Callable[..., Branch]:
    """Return a factory that creates a :class:`Branch`."""

    def _factory(*, company: Company | None = None, code: str | None = None, **kwargs: Any) -> Branch:
        return Branch.objects.create(
            company=company or make_company(),
            name=kwargs.pop("name", f"Test Branch {uuid4().hex[:6]}"),
            code=code or _next_branch_code(),
            timezone=kwargs.pop("timezone", "UTC"),
            operational_day_cutoff=kwargs.pop("operational_day_cutoff", time(6, 0)),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_membership(db, make_user, make_company) -> Callable[..., CompanyMembership]:
    """Return a factory that creates a :class:`CompanyMembership`.

    Defaults to the OWNER role. Pass ``user=`` or ``company=`` to attach to
    existing records.
    """

    def _factory(
        *,
        role: str = CompanyRole.OWNER,
        user: User | None = None,
        company: Company | None = None,
        active: bool = True,
        **kwargs: Any,
    ) -> CompanyMembership:
        return CompanyMembership.objects.create(
            user=user or make_user(),
            company=company or make_company(),
            role=role,
            active=active,
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_job_role(db, make_company) -> Callable[..., JobRole]:
    """Return a factory that creates a :class:`JobRole` for a company."""

    def _factory(*, company: Company | None = None, name: str = "Staff", code: str | None = None, **kwargs: Any) -> JobRole:
        return JobRole.objects.create(
            company=company or make_company(),
            name=name,
            code=code or f"role-{uuid4().hex[:6]}",
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_branch_membership(db, make_user, make_company, make_branch, make_job_role) -> Callable[..., UserBranchMembership]:
    """Return a factory that creates a :class:`UserBranchMembership`."""

    def _factory(
        *,
        user: User | None = None,
        company: Company | None = None,
        branch: Branch | None = None,
        job_role: JobRole | None = None,
        **kwargs: Any,
    ) -> UserBranchMembership:
        _company = company or make_company()
        return UserBranchMembership.objects.create(
            user=user or make_user(),
            company=_company,
            branch=branch or make_branch(company=_company),
            job_role=job_role or make_job_role(company=_company),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_template(db, make_company, make_branch) -> Callable[..., TaskTemplate]:
    """Return a factory that creates a :class:`TaskTemplate`."""

    def _factory(
        *,
        company: Company | None = None,
        branch: Branch | None = None,
        slug: str | None = None,
        name: str = "Daily Task",
        assigned_user: User | None = None,
        **kwargs: Any,
    ) -> TaskTemplate:
        _company = company or make_company()
        return TaskTemplate.objects.create(
            company=_company,
            branch=branch or make_branch(company=_company),
            slug=slug or f"task-{uuid4().hex[:6]}",
            name=name,
            assignment_mode=kwargs.pop("assignment_mode", TaskAssignmentMode.NAMED_USER),
            assigned_user=kwargs.pop("assigned_user", assigned_user),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_template_version(db, make_template) -> Callable[..., TaskTemplateVersion]:
    """Return a factory that creates a :class:`TaskTemplateVersion`."""

    def _factory(
        *,
        template: TaskTemplate | None = None,
        version_number: int = 1,
        instructions: str = "Do work",
        **kwargs: Any,
    ) -> TaskTemplateVersion:
        return TaskTemplateVersion.objects.create(
            template=template or make_template(),
            version_number=version_number,
            instructions=instructions,
            checklist_definition=kwargs.pop("checklist_definition", []),
            evidence_requirements=kwargs.pop("evidence_requirements", []),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_schedule(db, make_company, make_branch, make_template) -> Callable[..., TaskSchedule]:
    """Return a factory that creates a :class:`TaskSchedule`.

    Defaults to a daily schedule at 09:00. Call ``schedule_due_tasks(...)``
    afterwards to materialise :class:`TaskInstance` rows.
    """

    def _factory(
        *,
        company: Company | None = None,
        branch: Branch | None = None,
        template: TaskTemplate | None = None,
        recurrence_type: str = TaskRecurrenceType.DAILY_FIXED,
        scheduled_time: time | None = None,
        **kwargs: Any,
    ) -> TaskSchedule:
        _company = company or make_company()
        return TaskSchedule.objects.create(
            company=_company,
            branch=branch or make_branch(company=_company),
            template=template or make_template(company=_company),
            recurrence_type=recurrence_type,
            scheduled_time=scheduled_time or time(9, 0),
            **kwargs,
        )

    return _factory


def _create_task_instance(
    company: Company,
    branch: Branch,
    template: TaskTemplate,
    **kwargs: Any,
) -> TaskInstance:
    """Create a :class:`TaskInstance` directly.

    Internal helper used by ``make_capture_session`` and ``make_evidence_item``
    when the caller has not supplied an existing ``task_instance=`` argument.
    Kept module-private (no leading ``_factory``) because the public surface
    is the two factories that wrap it; tests do not need a stand-alone
    ``make_task_instance`` fixture.
    """
    template_version = template.versions.first() if template.versions.exists() else None
    if template_version is None:
        # The conftest factory is invoked before ``make_template_version``
        # is set up, so we cannot rely on it being available here. We
        # create a placeholder version inline so the helper remains
        # backward-compatible with the old API while satisfying the
        # ``NOT NULL`` constraint on ``template_version_id``.
        from apps.tasks.models import TaskTemplateVersion

        template_version = TaskTemplateVersion.objects.create(
            template=template,
            version_number=1,
            instructions="placeholder",
        )
    return TaskInstance.objects.create(
        company=company,
        branch=branch,
        template=template,
        template_version=template_version,
        scheduled_for=kwargs.pop("scheduled_for", timezone.now()),
        due_at=kwargs.pop("due_at", timezone.now()),
        **kwargs,
    )


@pytest.fixture
def make_capture_session(db, make_company, make_branch, make_user) -> Callable[..., CaptureSession]:
    """Return a factory that creates a :class:`CaptureSession`.

    If no ``task_instance`` is supplied, a new :class:`TaskInstance` is created
    via the internal helper. The factory will reuse an existing instance for
    the same company/branch if one already exists (e.g. materialised by
    ``schedule_due_tasks``) so that evidence attaches to the right instance.
    """

    def _factory(
        *,
        company: Company | None = None,
        branch: Branch | None = None,
        task_instance: TaskInstance | None = None,
        created_by: User | None = None,
        evidence_type: str = EvidenceType.IMAGE,
        token: str | None = None,
        expires_at: Any = None,
        **kwargs: Any,
    ) -> CaptureSession:
        _company = company or make_company()
        _branch = branch or make_branch(company=_company)
        if task_instance is None:
            existing = TaskInstance.objects.filter(company=_company, branch=_branch).order_by("created_at").first()
            if existing is not None:
                _instance = existing
            else:
                _template = TaskTemplate.objects.filter(company=_company, branch=_branch).order_by("created_at").first()
                if _template is None:
                    raise ValueError(
                        "make_capture_session needs either a task_instance= "
                        "or an existing TaskTemplate/TaskInstance for the branch."
                    )
                _instance = _create_task_instance(_company, _branch, _template)
        else:
            _instance = task_instance
        return CaptureSession.objects.create(
            company=_company,
            branch=_branch,
            task_instance=_instance,
            template_version=_instance.template_version,
            created_by=created_by or make_user(),
            evidence_type=evidence_type,
            token=token or f"capture-{uuid4().hex[:8]}",
            expires_at=expires_at or timezone.now(),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_evidence_item(
    db, make_company, make_branch, make_user, make_capture_session
) -> Callable[..., EvidenceItem]:
    """Return a factory that creates an :class:`EvidenceItem`."""

    def _factory(
        *,
        company: Company | None = None,
        branch: Branch | None = None,
        task_instance: TaskInstance | None = None,
        capture_session: CaptureSession | None = None,
        submitted_by: User | None = None,
        evidence_type: str = EvidenceType.IMAGE,
        private_media_name: str | None = None,
        blurred_media_name: str | None = None,
        **kwargs: Any,
    ) -> EvidenceItem:
        _company = company or make_company()
        _branch = branch or make_branch(company=_company)
        _capture = capture_session or make_capture_session(
            company=_company, branch=_branch, task_instance=task_instance
        )
        return EvidenceItem.objects.create(
            company=_company,
            branch=_branch,
            task_instance=_capture.task_instance,
            capture_session=_capture,
            submitted_by=submitted_by or make_user(),
            evidence_type=evidence_type,
            private_media_name=private_media_name or f"private-{uuid4().hex[:6]}.webp",
            blurred_media_name=blurred_media_name or f"blurred-{uuid4().hex[:6]}.webp",
            **kwargs,
        )

    return _factory


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def force_login_company(db, make_company):
    """Return a helper that logs a user in and binds the company to the session.

    Replaces the recurring pattern::

        client = Client()
        client.force_login(user, backend="...")
        session = client.session
        session["company_id"] = str(company.id)
        session.save()

    Usage::

        def test_x(force_login_company, make_user, make_company):
            user = make_user()
            company = make_company(owner=user)
            client = force_login_company(user, company)
            response = client.get("/api/v1/...")
    """

    def _factory(user: User, company: Company) -> Client:
        client = Client()
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        session = client.session
        session["company_id"] = str(company.id)
        session.save()
        return client

    return _factory
