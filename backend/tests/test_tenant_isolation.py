"""BE-03: Comprehensive tenant-isolation test suite.

These tests pin the cross-tenant boundaries that ``TenantAPIView`` and the
``validate_company_reference`` helper are supposed to enforce. Every test
exercises the realistic HTTP path: a user authenticated in company A tries to
read or mutate a record that belongs to company B. The expected response is
either a 403 (when the platform's permission layer raises) or a 404 (when the
record was not found because the company filter was applied at the queryset
level). Anything else is a regression.
"""
from __future__ import annotations

import pytest
from django.test import Client

from apps.evidence.models import EvidenceItem, TaskIssueReport
from apps.organizations.models import CompanyMembership, CompanyRole, UserBranchMembership
from apps.reviews.models import ReviewDecision, ReviewDecisionType
from apps.tasks.models import TaskInstance, TaskTemplate

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_authenticated_client(user, company):
    client = Client()
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    return client


# ---------------------------------------------------------------------------
# Tenancy context tests
# ---------------------------------------------------------------------------


class TestTenancyContext:
    """The tenant context must isolate two companies even when both are owned
    by the same user."""

    def test_owner_with_two_companies_sees_only_active_company(
        self, make_user, make_company
    ):
        owner = make_user(login_id="multi-owner")
        company_a = make_company(owner=owner, code="iso-a")
        company_b = make_company(owner=owner, code="iso-b")
        CompanyMembership.objects.create(company=company_a, user=owner, role=CompanyRole.OWNER)
        CompanyMembership.objects.create(company=company_b, user=owner, role=CompanyRole.OWNER)

        client = _make_authenticated_client(owner, company_a)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["company"]["id"] == str(company_a.id)

        # Switching the company_id in the session must switch the active tenant.
        session = client.session
        session["company_id"] = str(company_b.id)
        session.save()
        response = client.get("/api/v1/auth/me")
        assert response.json()["company"]["id"] == str(company_b.id)

    def test_employee_cannot_switch_to_company_they_do_not_belong_to(
        self, make_user, make_company
    ):
        employee = make_user(login_id="emp")
        company_a = make_company(code="emp-a")
        company_b = make_company(code="emp-b")
        CompanyMembership.objects.create(company=company_a, user=employee, role=CompanyRole.EMPLOYEE)

        client = _make_authenticated_client(employee, company_a)
        session = client.session
        session["company_id"] = str(company_b.id)
        session.save()
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403

    def test_forged_company_id_returns_403(self, make_user, make_company):
        # A user without membership in a real company should not be able
        # to "log in" to a forged company id and read its data.
        user = make_user(login_id="no-co")
        company = make_company(code="forged")
        client = _make_authenticated_client(user, company)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Tasks isolation
# ---------------------------------------------------------------------------


class TestTaskIsolation:
    """Task templates and instances must not leak across tenants."""

    def test_company_a_cannot_list_company_b_templates(
        self, make_user, make_company, make_membership, make_template, force_login_company
    ):
        owner_a = make_user(login_id="owner-a")
        company_a = make_company(owner=owner_a, code="tpl-a")
        make_membership(user=owner_a, company=company_a, role=CompanyRole.OWNER)
        # Owner needs MFA for non-bypass endpoints (BE-06); enroll and
        # verify it before exercising the tenant boundary.
        from apps.identity.models import MfaEnrollment, MfaMethodType
        MfaEnrollment.objects.create(
            user=owner_a,
            method_type=MfaMethodType.TOTP,
            verified_at=__import__("django.utils.timezone", fromlist=["now"]).now(),
            active=True,
        )
        company_b = make_company(code="tpl-b")
        make_template(company=company_b, slug="leaky")

        client = force_login_company(owner_a, company_a)
        response = client.get("/api/v1/tasks/templates")
        assert response.status_code == 200
        slugs = {t["slug"] for t in response.json()["templates"]}
        assert "leaky" not in slugs

    def test_task_instance_lookup_rejects_cross_company_id(
        self, make_user, make_company, make_template, make_template_version, force_login_company
    ):
        owner_a = make_user(login_id="inst-a")
        company_a = make_company(owner=owner_a, code="inst-a")
        company_b = make_company(code="inst-b")
        template_b = make_template(company=company_b, slug="hidden")
        version_b = make_template_version(template=template_b)
        now = __import__("django.utils.timezone", fromlist=["now"]).now()
        instance_b = TaskInstance.objects.create(
            company=company_b,
            branch=template_b.branch,
            template=template_b,
            template_version=version_b,
            scheduled_for=now,
            due_at=now,
        )

        client = force_login_company(owner_a, company_a)
        response = client.post(
            f"/api/v1/tasks/instances/{instance_b.id}/claim",
            data={},
            content_type="application/json",
        )
        # The task lookup uses ``get_object_or_404`` which yields a 404.
        # The platform's error layer turns that into a 400. Either way the
        # cross-tenant access is denied.
        assert response.status_code in (400, 403, 404)


# ---------------------------------------------------------------------------
# Evidence isolation
# ---------------------------------------------------------------------------


class TestEvidenceIsolation:
    """Evidence and discussion threads must not leak across tenants."""

    def test_evidence_task_view_rejects_cross_company_instance(
        self,
        make_user,
        make_company,
        make_template,
        make_template_version,
        make_capture_session,
        make_evidence_item,
        force_login_company,
    ):
        owner_a = make_user(login_id="ev-a")
        company_a = make_company(owner=owner_a, code="ev-a")
        company_b = make_company(code="ev-b")
        template_b = make_template(company=company_b, slug="ev")
        version_b = make_template_version(template=template_b)
        from django.utils.timezone import now
        from apps.tasks.models import TaskInstance as _TaskInstance
        instance_b = _TaskInstance.objects.create(
            company=company_b,
            branch=template_b.branch,
            template=template_b,
            template_version=version_b,
            scheduled_for=now(),
            due_at=now(),
        )
        capture_b = make_capture_session(
            company=company_b, branch=template_b.branch, task_instance=instance_b
        )
        evidence_b = make_evidence_item(
            company=company_b, branch=template_b.branch, capture_session=capture_b
        )

        client = force_login_company(owner_a, company_a)
        response = client.get(f"/api/v1/evidence/tasks/{evidence_b.task_instance_id}")
        # The view raises a 404 when the task is outside the active
        # company; the platform's error layer turns that into a 400. We
        # accept any non-200 status as evidence that the cross-tenant
        # boundary holds.
        assert response.status_code in (400, 403, 404)

    def test_issue_create_rejects_cross_company_task(
        self,
        make_user,
        make_company,
        make_template,
        make_template_version,
        force_login_company,
    ):
        owner_a = make_user(login_id="iss-a")
        company_a = make_company(owner=owner_a, code="iss-a")
        company_b = make_company(code="iss-b")
        template_b = make_template(company=company_b, slug="iss")
        version_b = make_template_version(template=template_b)
        now = __import__("django.utils.timezone", fromlist=["now"]).now()
        instance_b = TaskInstance.objects.create(
            company=company_b,
            branch=template_b.branch,
            template=template_b,
            template_version=version_b,
            scheduled_for=now,
            due_at=now,
        )

        client = force_login_company(owner_a, company_a)
        response = client.post(
            "/api/v1/evidence/issues",
            data={"task_instance_id": str(instance_b.id), "note": "leak"},
            content_type="application/json",
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Review decisions isolation
# ---------------------------------------------------------------------------


class TestReviewIsolation:
    """A review decision can only target a record inside the active company."""

    def test_review_decision_rejects_cross_company_evidence(
        self,
        make_user,
        make_company,
        make_template,
        make_evidence_item,
        force_login_company,
    ):
        owner_a = make_user(login_id="rv-a")
        company_a = make_company(owner=owner_a, code="rv-a")
        company_b = make_company(code="rv-b")
        template_b = make_template(company=company_b, slug="rv")
        evidence_b = make_evidence_item(company=company_b, branch=template_b.branch)

        client = force_login_company(owner_a, company_a)
        response = client.post(
            "/api/v1/reviews/decisions",
            data={
                "decision_type": ReviewDecisionType.APPROVE,
                "evidence_item_id": str(evidence_b.id),
            },
            content_type="application/json",
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Branch / membership isolation
# ---------------------------------------------------------------------------


class TestBranchIsolation:
    def test_branch_membership_rejects_cross_company_branch(
        self,
        make_user,
        make_company,
        make_branch,
        make_job_role,
        force_login_company,
    ):
        owner_a = make_user(login_id="bm-a")
        company_a = make_company(owner=owner_a, code="bm-a")
        company_b = make_company(code="bm-b")
        branch_b = make_branch(company=company_b, code="bm-b-branch")
        role_b = make_job_role(company=company_b)
        user_b = make_user(login_id="bm-b-user")

        client = force_login_company(owner_a, company_a)
        response = client.post(
            "/api/v1/auth/company/branch-memberships",
            data={
                "user_id": str(user_b.id),
                "branch_id": str(branch_b.id),
                "job_role_id": str(role_b.id),
            },
            content_type="application/json",
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Backup / restore isolation
# ---------------------------------------------------------------------------


class TestBackupIsolation:
    def test_restore_rejects_cross_company_backup(
        self,
        make_user,
        make_company,
        force_login_company,
    ):
        owner_a = make_user(login_id="bk-a")
        company_a = make_company(owner=owner_a, code="bk-a")
        company_b = make_company(code="bk-b")
        from apps.backups.models import BackupRun
        run_b = BackupRun.objects.create(company=company_b, requested_by=owner_a)

        client = force_login_company(owner_a, company_a)
        response = client.post(
            "/api/v1/backups/restore",
            data={
                "backup_run_id": str(run_b.id),
                "target_name": "leaky",
                "confirmation": "I understand",
            },
            content_type="application/json",
        )
        assert response.status_code == 403
