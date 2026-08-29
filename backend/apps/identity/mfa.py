"""Identity helpers: MFA verification checks.

The platform requires a verified TOTP enrollment for any user that
holds a privileged role (Platform Admin or company Owner). The check
is implemented here once and reused by the login view, the MFA
enforcement middleware, and the management commands.
"""
from __future__ import annotations

from apps.identity.models import MfaEnrollment, MfaMethodType, User
from apps.organizations.models import CompanyMembership, CompanyRole
from apps.tenancy.models import Company
from django.db.models import Q
from django.utils import timezone


def has_verified_mfa(user: User) -> bool:
    """Return ``True`` if the user has at least one verified TOTP enrollment."""
    if not user.is_authenticated:
        return False
    return MfaEnrollment.objects.filter(
        user=user,
        method_type=MfaMethodType.TOTP,
        active=True,
        verified_at__isnull=False,
    ).exists()


def user_requires_mfa(user: User, company: Company | None = None) -> bool:
    """Return ``True`` if MFA is mandatory for ``user`` in the active company.

    Platform staff (``is_staff`` or ``is_superuser``) and the owner of the
    active company are required to enroll MFA. Employees in a non-owner
    role fall back to the historical "optional MFA" policy.
    """
    if not user.is_authenticated:
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    if company is None:
        return False
    if company.owner_id == getattr(user, "id", None):
        return True
    return CompanyMembership.objects.filter(
        Q(active_until__isnull=True) | Q(active_until__gt=timezone.now()),
        company=company,
        user=user,
        active=True,
        role=CompanyRole.OWNER,
    ).exists()
