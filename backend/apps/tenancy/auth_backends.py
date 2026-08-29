from __future__ import annotations

from django.contrib.auth.backends import BaseBackend

from apps.audit.services import record_audit_event
from apps.identity.models import MfaEnrollment, MfaMethodType, User

from .models import Company, CompanyStatus
from .services import current_support_authorization
from apps.organizations.models import CompanyMembership
from .access import active_membership_q


def _record_failed_login(*, request, company_code: str, login_id: str, reason: str) -> None:
    """BE-05: record every failed login attempt for audit and rate-limiting."""
    try:
        record_audit_event(
            event_type="LOGIN_FAILED",
            target_type="user",
            target_id=login_id or "",
            actor_id="",
            metadata={
                "company_code": company_code or "",
                "reason": reason,
                "remote_addr": (request.META.get("REMOTE_ADDR") if request else "") or "",
            },
        )
    except Exception:  # pragma: no cover - audit must never block auth
        # The audit record is best-effort; the failure is still
        # surfaced to the caller via the ``reason`` text.
        pass


class CompanyCodeBackend(BaseBackend):
    def authenticate(self, request, company_code=None, login_id=None, password=None, **kwargs):
        if not company_code or not login_id or password is None:
            _record_failed_login(request=request, company_code=company_code or "", login_id=login_id or "", reason="missing_fields")
            return None
        try:
            company = Company.objects.get(code=company_code)
        except Company.DoesNotExist:
            _record_failed_login(request=request, company_code=company_code, login_id=login_id, reason="unknown_company")
            return None
        if company.status in {CompanyStatus.SUSPENDED, CompanyStatus.PENDING_DELETION, CompanyStatus.DELETED}:
            _record_failed_login(request=request, company_code=company_code, login_id=login_id, reason="inactive_company")
            return None
        try:
            user = User.objects.get(login_id=login_id)
        except User.DoesNotExist:
            _record_failed_login(request=request, company_code=company_code, login_id=login_id, reason="unknown_user")
            return None
        if not user.check_password(password):
            _record_failed_login(request=request, company_code=company_code, login_id=login_id, reason="bad_password")
            return None
        active_membership_exists = CompanyMembership.objects.filter(
            company=company,
            user=user,
            active=True,
        ).filter(active_membership_q()).exists()
        owner_has_memberships = CompanyMembership.objects.filter(company=company, user=user).exists()
        if active_membership_exists or (company.owner_id == user.id and not owner_has_memberships):
            return user
        if current_support_authorization(company, user) is None:
            _record_failed_login(request=request, company_code=company_code, login_id=login_id, reason="not_authorized_for_company")
            return None
        if not MfaEnrollment.objects.filter(
            user=user,
            method_type=MfaMethodType.TOTP,
            active=True,
            verified_at__isnull=False,
        ).exists():
            _record_failed_login(request=request, company_code=company_code, login_id=login_id, reason="missing_mfa_enrollment")
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
