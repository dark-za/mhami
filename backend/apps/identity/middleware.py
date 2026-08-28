"""BE-06: MFA enforcement middleware.

The platform requires a verified TOTP enrollment for any user that
holds a privileged role (Platform Admin or company Owner). The
middleware short-circuits any request whose user falls in that bucket
but does not yet have MFA verified, redirecting them to the enrollment
endpoints instead.

The middleware deliberately keeps the bypass list small and explicit:
the MFA enroll/verify endpoints, the ``/me`` introspection endpoint
(so the client can decide where to send the user), and the public
auth/health surfaces. Adding to the bypass list is a code change that
must be reviewed.

The enforcement can be disabled globally by setting
``MFA_ENFORCEMENT_ENABLED = False`` in the project settings. The test
suite relies on this knob to avoid having to enroll MFA for every
test user.
"""
from __future__ import annotations

from typing import Callable

from django.conf import settings
from django.http import JsonResponse

from apps.identity.mfa import has_verified_mfa, user_requires_mfa
from apps.tenancy.models import Company


BYPASS_PREFIXES: tuple[str, ...] = (
    "/api/v1/auth/mfa",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/logout",
    "/api/v1/auth/me",
    "/api/health",
)


def _enforcement_enabled() -> bool:
    return bool(getattr(settings, "MFA_ENFORCEMENT_ENABLED", True))


class MFAEnforcementMiddleware:
    """Block privileged users that have not completed MFA setup."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        if not _enforcement_enabled():
            return self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            path = request.path or ""
            if not any(path.startswith(prefix) for prefix in BYPASS_PREFIXES):
                company = self._active_company(request)
                if user_requires_mfa(user, company) and not has_verified_mfa(user):
                    return JsonResponse(
                        {
                            "error": {
                                "code": "MFA_ENROLLMENT_REQUIRED",
                                "message": (
                                    "MFA enrollment is required for "
                                    "Platform Admin or company Owner accounts."
                                ),
                            }
                        },
                        status=403,
                    )
        return self.get_response(request)

    @staticmethod
    def _active_company(request) -> Company | None:
        company_id = request.session.get("company_id")
        if not company_id:
            return None
        return Company.objects.filter(id=company_id).first()
