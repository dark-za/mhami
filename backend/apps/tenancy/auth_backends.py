from __future__ import annotations

from django.contrib.auth.backends import BaseBackend

from apps.audit.services import record_audit_event
from apps.identity.models import User

from .models import Company, CompanyStatus
from apps.organizations.models import CompanyMembership
from .access import active_membership_q


def _record_failed_login(*, request, login_id: str, reason: str) -> None:
    """BE-05: record every failed login attempt for audit and rate-limiting."""
    try:
        record_audit_event(
            event_type="LOGIN_FAILED",
            target_type="user",
            target_id=login_id or "",
            actor_id="",
            metadata={
                "reason": reason,
                "remote_addr": (request.META.get("REMOTE_ADDR") if request else "") or "",
            },
        )
    except Exception:  # pragma: no cover - audit must never block auth
        # The audit record is best-effort; the failure is still
        # surfaced to the caller via the ``reason`` text.
        pass


def _sole_company_or_none(request) -> tuple[Company | None, str | None]:
    """Return (sole Company, failure_reason). Fail closed on 0 or >1 organizations."""
    companies = list(Company.objects.order_by("id")[:2])
    if not companies:
        _record_failed_login(request=request, login_id="", reason="no_organization")
        return None, "no_organization"
    if len(companies) > 1:
        _record_failed_login(request=request, login_id="", reason="multiple_organizations")
        return None, "multiple_organizations"
    company = companies[0]
    if company.status == CompanyStatus.SUSPENDED:
        _record_failed_login(request=request, login_id="", reason="inactive_company")
        return None, "inactive_company"
    if not company.is_operational():
        _record_failed_login(request=request, login_id="", reason="inactive_company")
        return None, "inactive_company"
    return company, None


class LocalInstallationBackend(BaseBackend):
    """Authenticate local users against the single installed organization.

    The organization is resolved by the server. No client-supplied tenant
    selector participates in authentication.
    """

    def authenticate(self, request, login_id=None, password=None, **kwargs):
        if not login_id or password is None:
            _record_failed_login(request=request, login_id=login_id or "", reason="missing_fields")
            return None

        company, failure = _sole_company_or_none(request)
        if company is None:
            # _sole_company_or_none already audited; add login_id-specific event as well
            if failure in {"no_organization", "multiple_organizations", "inactive_company"}:
                _record_failed_login(request=request, login_id=login_id or "", reason=failure)
            return None

        try:
            user = User.objects.get(login_id=login_id)
        except User.DoesNotExist:
            _record_failed_login(request=request, login_id=login_id, reason="unknown_user")
            return None
        if not user.check_password(password):
            _record_failed_login(request=request, login_id=login_id, reason="bad_password")
            return None
        if not user.is_active:
            _record_failed_login(request=request, login_id=login_id, reason="inactive_user")
            return None
        active_membership_exists = CompanyMembership.objects.filter(
            company=company,
            user=user,
            active=True,
        ).filter(active_membership_q()).exists()
        owner_has_memberships = CompanyMembership.objects.filter(company=company, user=user).exists()
        if active_membership_exists or (company.owner_id == user.id and not owner_has_memberships):
            return user
        _record_failed_login(request=request, login_id=login_id, reason="not_authorized_for_company")
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None


class CompanyCodeBackend(LocalInstallationBackend):
    """Backward-compatible import path for sessions created before this release."""

    pass
