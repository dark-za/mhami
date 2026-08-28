"""Service-side enforcement helpers for re-acceptance after a legal update.

The :class:`LegalAcceptanceRequired` decorator is the runtime
counterpart of :func:`apps.compliance.acceptance.require_current_acceptance`.
It is intended for use on owner-only management endpoints (e.g.
``/api/v1/auth/company/members``) where a missing acceptance for the
current published version must block the operation.

The decorator raises :class:`apps.platform_core.errors.PlatformLegalBlockException`
(HTTP 451, "Unavailable For Legal Reasons"). The error payload
includes the list of missing kinds so the client can route the user
to the acceptance endpoint.

This module is intentionally separate from :mod:`apps.compliance.acceptance`
so the platform can adopt the enforcement gradually — endpoints opt in
explicitly, rather than every view silently enforcing re-acceptance.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from apps.platform_core.errors import PlatformLegalBlockException

from .acceptance import require_current_acceptance

_P = ParamSpec("_P")
_R = TypeVar("_R")


def LegalAcceptanceRequired(
    *,
    kinds: tuple[str, ...] | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Block a view unless the tenant holds current legal acceptances.

    Args:
        kinds: Optional tuple of ``LegalDocumentType`` values to check.
            Defaults to all kinds for which a document is currently
            published.

    Returns:
        A decorator that wraps the view method and raises
        :class:`PlatformLegalBlockException` (HTTP 451) when the active
        tenant is missing one or more current acceptances.
    """

    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(func)
        def wrapper(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            from apps.organizations.models import CompanyRole
            from apps.tenancy.access import tenant_context
            from apps.tenancy.models import CompanyMembership

            request = getattr(self, "request", None)
            tenant_getter = getattr(self, "get_tenant", None)
            company = None
            if callable(tenant_getter):
                try:
                    company = tenant_getter().company
                except Exception:  # noqa: BLE001 - fall back to session lookup
                    company = None
            if company is None and request is not None:
                try:
                    context = tenant_context(request)
                    company = context.company
                except Exception:  # noqa: BLE001 - no tenant is fine
                    company = None
            if company is None and request is not None and getattr(request, "user", None) is not None:
                # Fall back to any active membership so re-acceptance is
                # enforced even before the tenant context is fully wired.
                membership = (
                    CompanyMembership.objects.filter(
                        user=request.user, active=True, role=CompanyRole.OWNER
                    )
                    .select_related("company")
                    .order_by("-active_from")
                    .first()
                )
                if membership is not None:
                    company = membership.company
            if company is None:
                # No tenant scope: nothing to enforce. The view's own
                # authentication/authorization will reject the request.
                return func(self, *args, **kwargs)
            try:
                require_current_acceptance(company, kinds=kinds)
            except Exception as exc:  # noqa: BLE001 - convert to API error
                missing = getattr(exc, "missing_kinds", [])
                raise PlatformLegalBlockException(missing_kinds=missing) from exc
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
