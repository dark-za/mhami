"""Tenancy service layer.

This module contains server-side operations for the local organization and
membership. It is the authoritative source of ownership checks.

Public functions follow a uniform shape:
- Keyword-only arguments after the leading positional model instance.
- Explicit return types.
"""

from __future__ import annotations

from secrets import choice
from string import ascii_lowercase, digits

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from apps.identity.models import User
from apps.organizations.models import CompanyMembership, CompanyRole
from .models import Company, CompanyStatus, InstallationState, LegalAcceptance, LegalDocumentType


class InstallationAlreadyConfiguredError(ValueError):
    """Raised when a caller tries to initialize an existing installation."""


def initial_setup_required() -> bool:
    """Return whether the installation still has no organization.

    The database is authoritative. Once the singleton is marked configured,
    browser setup never reopens even if a damaged database later loses its
    company row.
    """

    if Company.objects.exists():
        return False
    state = InstallationState.objects.filter(pk=1).first()
    if state is not None:
        return not state.is_configured
    return _empty_installation_can_recover()


def _empty_installation_can_recover() -> bool:
    from apps.audit.models import AuditEvent

    return not User.objects.exists() and not AuditEvent.objects.exists()


def provision_initial_owner(
    *,
    organization_name: str,
    owner_login_id: str,
    owner_display_name: str,
    password: str,
    initiated_via: str,
) -> tuple[Company, User]:
    """Create the sole organization and its owner exactly once.

    Both the CLI command and the browser setup endpoint call this service so
    the one-organization invariant cannot drift between entry points.
    """

    org_name = organization_name.strip()
    login_id = owner_login_id.strip()
    display_name = owner_display_name.strip()
    if not org_name:
        raise ValueError("Organization name is required.")
    if not login_id:
        raise ValueError("Owner login ID is required.")
    if not password:
        raise ValueError("A non-empty owner password is required.")
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise ValueError("; ".join(exc.messages)) from exc

    try:
        code = normalize_company_code(org_name)
    except ValueError as exc:
        raise ValueError("Organization name must include letters or numbers.") from exc

    with transaction.atomic():
        # A database flush removes migration-seeded rows. Recover only an
        # empty installation; retained users or audit history require review.
        if not InstallationState.objects.filter(pk=1).exists():
            if Company.objects.exists() or not _empty_installation_can_recover():
                raise InstallationAlreadyConfiguredError("Installation state requires operator recovery.")
            InstallationState.objects.get_or_create(pk=1)
        state = InstallationState.objects.select_for_update().get(pk=1)
        if state.is_configured or Company.objects.exists():
            raise InstallationAlreadyConfiguredError(
                "An organization already exists. Initial setup cannot create another organization."
            )
        if User.objects.filter(login_id=login_id).exists():
            raise ValueError("This login ID is already in use.")

        owner = User.objects.create_user(
            login_id=login_id,
            password=password,
            display_name=display_name,
        )
        company = Company.objects.create(
            name=org_name,
            code=code,
            industry="other",
            owner=owner,
            status=CompanyStatus.ACTIVE,
        )
        CompanyMembership.objects.create(company=company, user=owner, role=CompanyRole.OWNER)

        # Record the initial local acceptance when the registry is available.
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

        state.configured_at = timezone.now()
        state.save(update_fields=["configured_at"])

        from apps.audit.services import record_audit_event

        record_audit_event(
            event_type="INSTALLATION_INITIALIZED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(owner.id),
            metadata={"initiated_via": initiated_via},
        )

    return company, owner


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


def _resolve_initial_acceptance_versions() -> tuple[str, str]:
    """Return the ``(terms_version, privacy_version)`` pair for a new tenant.

    The function consults the :class:`apps.compliance.models.LegalDocument`
    registry when the compliance app is available. When no document is
    currently published for a kind, the historical default ``"v1"`` is
    used during initial local provisioning before legal text is published.
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
    from apps.tenancy.access import active_membership_q

    membership = (
        CompanyMembership.objects.select_related("company")
        .filter(user=user, active=True)
        .filter(active_membership_q())
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
    from apps.tenancy.access import has_company_role

    return has_company_role(company, user, str(CompanyRole.OWNER))


def ensure_company_operational(company: Company) -> None:
    """Raise :class:`ValueError` if the company is not in a writable state.

    Only :attr:`CompanyStatus.ACTIVE` companies are writable. ``SUSPENDED``
    is a local owner-controlled safety switch and fails this check so
    mutations are short-circuited at the service layer.
    """
    if not company.is_operational():
        raise ValueError("Company is read-only or unavailable for operational changes.")
