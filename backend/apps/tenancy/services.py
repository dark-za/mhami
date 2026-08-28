"""Tenancy service layer.

This module contains every server-side operation that touches a
:class:`~apps.tenancy.models.Company`, :class:`CompanyMembership`,
:class:`SupportAuthorization`, or MFA enrollment. It is the single
authoritative source of business rules for tenant lifecycle, ownership
checks, and platform support access.

Public functions follow a uniform shape:
- Keyword-only arguments after the leading positional model instance.
- Explicit return types.
- Audit + outbox events emitted via the ``@audited_service`` decorator
  when the change is single-step; complex multi-field updates use an
  inline ``record_audit_event`` call so the ``before`` snapshot is
  preserved.
"""

from __future__ import annotations

import base64
import secrets
from datetime import timedelta
from secrets import choice
from string import ascii_lowercase, digits

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.identity.models import MfaEnrollment, MfaMethodType, User
from apps.organizations.models import CompanyMembership, CompanyRole
from apps.platform_core.service_base import audited_service

from .models import Company, CompanyStatus, LegalAcceptance, LegalDocumentType, SupportAuthorization


READ_ONLY_PERIOD = timedelta(days=90)
"""Duration a company remains in :attr:`CompanyStatus.READ_ONLY` before pending deletion."""


class InvalidCompanyLifecycleTransition(ValueError):
    """Raised when an unsupported company status transition is requested."""


_ALLOWED_LIFECYCLE_TRANSITIONS: dict[str, set[str]] = {
    CompanyStatus.TRIAL: {CompanyStatus.ACTIVE, CompanyStatus.SUSPENDED, CompanyStatus.READ_ONLY},
    CompanyStatus.ACTIVE: {CompanyStatus.SUSPENDED, CompanyStatus.READ_ONLY},
    CompanyStatus.SUSPENDED: {CompanyStatus.ACTIVE, CompanyStatus.READ_ONLY},
    CompanyStatus.READ_ONLY: {CompanyStatus.ACTIVE, CompanyStatus.PENDING_DELETION},
    CompanyStatus.PENDING_DELETION: {CompanyStatus.DELETED},
    CompanyStatus.DELETED: set(),
}


def normalize_company_code(code: str) -> str:
    """Normalise a user-supplied company code to a stable canonical form.

    Strips whitespace, lowercases, and keeps only alphanumerics plus
    ``-`` and ``_``. Raises :class:`ValueError` if the result is empty.

    Args:
        code: The raw user input (e.g. ``"Acme Co"``).

    Returns:
        The normalised code (e.g. ``"acme-co"``).
    """
    normalized = "".join(ch for ch in code.strip().lower() if ch.isalnum() or ch in {"-", "_"})
    if not normalized:
        raise ValueError("company_code is required")
    return normalized


def generate_company_code(length: int = 8) -> str:
    """Generate a random, lowercase, alphanumeric company code.

    Args:
        length: Number of characters to emit (default 8).

    Returns:
        A random code drawn from ``a-z`` and ``0-9``.
    """
    alphabet = ascii_lowercase + digits
    return "".join(choice(alphabet) for _ in range(length))


@audited_service(event_type="COMPANY_REGISTERED", target_type="company")
def register_company(
    *,
    company_name: str,
    company_code: str,
    industry: str,
    owner_login_id: str,
    owner_password: str,
    owner_display_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
) -> tuple[Company, User]:
    """Register a new company with an initial owner user.

    Creates the owner :class:`User`, the :class:`Company`, an
    :class:`CompanyMembership` with the OWNER role, and the two
    required :class:`LegalAcceptance` records (terms and privacy).

    Args:
        company_name: Display name for the company.
        company_code: Raw company code; will be normalised.
        industry: One of :class:`~apps.tenancy.models.IndustryChoice`.
        owner_login_id: Login id for the initial owner user.
        owner_password: Plaintext password (hashed on save).
        owner_display_name: Optional display name.
        contact_email: Optional contact email.
        contact_phone: Optional contact phone.

    Returns:
        A ``(company, owner)`` tuple.

    Side Effects:
        - Audit event ``COMPANY_REGISTERED`` with the new company as target.
        - Outbox event ``tenancy.company.created``.
    """
    owner = User.objects.create_user(
        login_id=owner_login_id,
        password=owner_password,
        display_name=owner_display_name,
    )
    company = Company.objects.create(
        name=company_name,
        code=normalize_company_code(company_code),
        industry=industry,
        owner=owner,
        contact_email=contact_email,
        contact_phone=contact_phone,
        trial_ends_at=timezone.now() + timedelta(days=30),
    )
    CompanyMembership.objects.create(company=company, user=owner, role=CompanyRole.OWNER)
    # LEGAL-06: the recorded acceptances must match the currently
    # published version of each document. When the ``apps.compliance``
    # registry is available, the helper resolves the live version;
    # otherwise the historical default ``"v1"`` is recorded so
    # self-registration continues to work before the legal text is
    # published.
    terms_version, privacy_version = _resolve_initial_acceptance_versions()
    LegalAcceptance.objects.create(
        company=company,
        accepted_by=owner,
        document_type=LegalDocumentType.TERMS,
        document_version=terms_version,
    )
    LegalAcceptance.objects.create(
        company=company,
        accepted_by=owner,
        document_type=LegalDocumentType.PRIVACY,
        document_version=privacy_version,
    )
    return company, owner


def _resolve_initial_acceptance_versions() -> tuple[str, str]:
    """Return the ``(terms_version, privacy_version)`` pair for a new tenant.

    The function consults the :class:`apps.compliance.models.LegalDocument`
    registry when the compliance app is available. When no document is
    currently published for a kind, the historical default ``"v1"`` is
    used so the registration flow continues to work before the legal
    text is published. The historical default is also recorded by
    ``record_pilot_acceptances`` so the staging environment stays in
    sync.
    """
    default = "v1"
    try:
        from apps.compliance.acceptance import LEGAL_TYPE_TO_KIND
        from apps.compliance.models import LegalDocumentKind
        from apps.compliance.services import current_legal_document
    except Exception:  # noqa: BLE001 - compliance app unavailable
        return default, default
    terms_version = default
    privacy_version = default
    if "terms" in LEGAL_TYPE_TO_KIND:
        document = current_legal_document(LegalDocumentKind(LEGAL_TYPE_TO_KIND["terms"]))
        if document is not None:
            terms_version = document.version
    if "privacy" in LEGAL_TYPE_TO_KIND:
        document = current_legal_document(LegalDocumentKind(LEGAL_TYPE_TO_KIND["privacy"]))
        if document is not None:
            privacy_version = document.version
    return terms_version, privacy_version


def user_company(user: User) -> Company | None:
    """Return the active company for a user, preferring the most recent membership.

    Args:
        user: The user to look up.

    Returns:
        The user's active :class:`Company` or ``None`` if the user has no
        active membership.
    """
    membership = (
        CompanyMembership.objects.select_related("company")
        .filter(user=user, active=True)
        .order_by("-active_from")
        .first()
    )
    return membership.company if membership else None


def is_owner(user: User, company: Company) -> bool:
    """Return ``True`` if the user holds the OWNER role for the company.

    The check covers both the explicit ``owner`` foreign key and any
    active OWNER memberships. Use this for read-side authorization only;
    mutations should go through :func:`apps.platform_core.mixins.TenantAPIView.get_tenant`.
    """
    return company.owner_id == user.id or CompanyMembership.objects.filter(
        company=company, user=user, role=CompanyRole.OWNER, active=True
    ).exists()


def ensure_company_operational(company: Company) -> None:
    """Raise :class:`ValueError` if the company is not in a writable state.

    Operational statuses are :attr:`CompanyStatus.TRIAL` and
    :attr:`CompanyStatus.ACTIVE`. READ_ONLY and PENDING_DELETION companies
    fail this check so mutations are short-circuited at the service layer.
    """
    if not company.is_operational():
        raise ValueError("Company is read-only or unavailable for operational changes.")


@transaction.atomic
def transition_company(
    company: Company,
    status: str,
    *,
    actor_id: str = "system",
    at=None,
) -> Company:
    """Transition a company's lifecycle status and emit an audit event.

    The audit event carries both ``before`` and ``after`` snapshots because
    the change touches three timestamp fields at once; we cannot use the
    generic :func:`audited_service` decorator here without losing the
    ``before`` payload. The transaction boundary is preserved.

    Args:
        company: The :class:`Company` to mutate. Mutated in place.
        status: The target :class:`CompanyStatus`.
        actor_id: Identifier of the actor; defaults to ``"system"`` for
            scheduled lifecycle processes.
        at: Optional timestamp for deterministic testing.

    Returns:
        The same ``company`` instance, refreshed after save.

    Raises:
        InvalidCompanyLifecycleTransition: If the transition is not
            permitted by :data:`_ALLOWED_LIFECYCLE_TRANSITIONS`.
    """
    now = at or timezone.now()
    if status == company.status:
        return company
    if status not in _ALLOWED_LIFECYCLE_TRANSITIONS[company.status]:
        raise InvalidCompanyLifecycleTransition(f"Cannot transition company from {company.status} to {status}.")

    before = {
        "status": company.status,
        "read_only_until": company.read_only_until.isoformat() if company.read_only_until else None,
        "deletion_due_at": company.deletion_due_at.isoformat() if company.deletion_due_at else None,
    }
    company.status = status
    update_fields = ["status", "updated_at"]
    if status == CompanyStatus.SUSPENDED:
        company.suspended_at = now
        update_fields.append("suspended_at")
    elif status == CompanyStatus.READ_ONLY:
        company.read_only_until = now + READ_ONLY_PERIOD
        company.deletion_due_at = company.read_only_until
        update_fields.extend(["read_only_until", "deletion_due_at"])
    elif status == CompanyStatus.ACTIVE:
        company.suspended_at = None
        company.read_only_until = None
        company.deletion_due_at = None
        update_fields.extend(["suspended_at", "read_only_until", "deletion_due_at"])
    elif status == CompanyStatus.PENDING_DELETION:
        company.deletion_due_at = now
        update_fields.append("deletion_due_at")

    with transaction.atomic():
        company.save(update_fields=update_fields)
        record_audit_event(
            event_type="COMPANY_LIFECYCLE_TRANSITIONED",
            target_type="company",
            target_id=str(company.id),
            actor_id=actor_id,
            before=before,
            after={
                "status": company.status,
                "read_only_until": company.read_only_until.isoformat() if company.read_only_until else None,
                "deletion_due_at": company.deletion_due_at.isoformat() if company.deletion_due_at else None,
            },
        )
    return company


def current_support_authorization(company: Company, support_user: User, *, at=None) -> SupportAuthorization | None:
    """Return the active, non-expired :class:`SupportAuthorization` for a support user.

    Args:
        company: The :class:`Company` the support user is accessing.
        support_user: The platform support user.
        at: Optional timestamp override (for deterministic tests).

    Returns:
        The matching authorization or ``None`` if no active grant exists.
    """
    return (
        SupportAuthorization.objects.filter(
            company=company,
            support_user=support_user,
            active=True,
            expires_at__gt=at or timezone.now(),
        )
        .order_by("-granted_at")
        .first()
    )


def has_current_support_authorization(company: Company, support_user: User, *, at=None) -> bool:
    """Return :func:`current_support_authorization` is not ``None``."""
    return current_support_authorization(company, support_user, at=at) is not None


def enroll_totp(user: User, label: str = "default") -> MfaEnrollment:
    """Enroll a user in TOTP-based MFA.

    Generates a 20-byte base32-encoded secret, stores it in an
    :class:`MfaEnrollment`, and returns the new record. The caller is
    responsible for rendering the QR code from the returned secret.

    Args:
        user: The :class:`User` to enroll.
        label: Optional user-defined label (default ``"default"``).

    Returns:
        The created :class:`MfaEnrollment`.
    """
    secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")
    enrollment = MfaEnrollment.objects.create(user=user, method_type=MfaMethodType.TOTP, label=label, secret=secret)
    return enrollment


@audited_service(event_type="SUPPORT_ACCESS_GRANTED", target_type="support_authorization")
def grant_support(
    company: Company,
    support_user: User,
    granted_by: User,
    *,
    reason: str,
    expires_at,
) -> SupportAuthorization:
    """Grant a support user temporary access to a company.

    Args:
        company: The :class:`Company` being accessed.
        support_user: The platform user who will receive support access.
        granted_by: The platform user authorising the grant.
        reason: Human-readable justification; must be non-blank.
        expires_at: When the grant should expire; must be in the future.

    Returns:
        The created :class:`SupportAuthorization`.

    Raises:
        ValueError: If ``reason`` is blank or ``expires_at`` is in the past.
    """
    if not reason.strip():
        raise ValueError("A support access reason is required.")
    if expires_at <= timezone.now():
        raise ValueError("Support access expiry must be in the future.")
    grant = SupportAuthorization.objects.create(
        company=company,
        support_user=support_user,
        granted_by=granted_by,
        reason=reason,
        expires_at=expires_at,
    )
    return grant


@audited_service(event_type="SUPPORT_ACCESS_REVOKED", target_type="support_authorization")
def revoke_support(grant: SupportAuthorization, *, revoked_by: User, at=None) -> SupportAuthorization:
    """Revoke a previously granted :class:`SupportAuthorization`.

    No-op if the grant is already inactive.

    Args:
        grant: The :class:`SupportAuthorization` to revoke.
        revoked_by: The :class:`User` performing the revocation.
        at: Optional timestamp override.

    Returns:
        The same ``grant`` after mutation.
    """
    if not grant.active:
        return grant
    grant.active = False
    grant.revoked_at = at or timezone.now()
    grant.save(update_fields=["active", "revoked_at"])
    return grant


def process_lifecycle_expirations(*, at=None, dry_run: bool = False) -> dict[str, int]:
    """Apply the daily lifecycle sweeps.

    Moves expired TRIAL companies to READ_ONLY, READ_ONLY companies to
    PENDING_DELETION, and expires any :class:`SupportAuthorization` whose
    ``expires_at`` has passed. Idempotent: re-running the same moment
    is a no-op.

    Args:
        at: Optional timestamp override for deterministic tests.
        dry_run: When ``True``, compute counts without mutating state.

    Returns:
        Counts of how many records would be / were transitioned, keyed
        by ``"read_only"``, ``"pending_deletion"``, ``"support_expired"``.

    Side Effects:
        - Transitions expired companies (one per ``select_for_update`` block).
        - Marks expired support grants inactive.
        - Audit event ``SUPPORT_ACCESS_EXPIRED`` per expired grant.
    """
    now = at or timezone.now()
    due_trials = Company.objects.filter(status=CompanyStatus.TRIAL, trial_ends_at__lte=now)
    due_read_only = Company.objects.filter(status=CompanyStatus.READ_ONLY, read_only_until__lte=now)
    expired_support = SupportAuthorization.objects.filter(active=True, expires_at__lte=now)
    result = {
        "read_only": due_trials.count(),
        "pending_deletion": due_read_only.count(),
        "support_expired": expired_support.count(),
    }
    if dry_run:
        return result

    for company_id in due_trials.values_list("id", flat=True):
        with transaction.atomic():
            company = Company.objects.select_for_update().get(id=company_id)
            if company.status == CompanyStatus.TRIAL and company.trial_ends_at <= now:
                transition_company(company, CompanyStatus.READ_ONLY, at=now)
    for company_id in due_read_only.values_list("id", flat=True):
        with transaction.atomic():
            company = Company.objects.select_for_update().get(id=company_id)
            if company.status == CompanyStatus.READ_ONLY and company.read_only_until <= now:
                transition_company(company, CompanyStatus.PENDING_DELETION, at=now)
    for grant_id in expired_support.values_list("id", flat=True):
        with transaction.atomic():
            grant = SupportAuthorization.objects.select_for_update().get(id=grant_id)
            if grant.active and grant.expires_at <= now:
                grant.active = False
                grant.save(update_fields=["active"])
                record_audit_event(
                    event_type="SUPPORT_ACCESS_EXPIRED",
                    target_type="support_authorization",
                    target_id=str(grant.id),
                    actor_id="system",
                    metadata={"company_id": str(grant.company_id), "support_user_id": str(grant.support_user_id)},
                )
    return result
