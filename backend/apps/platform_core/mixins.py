"""Reusable DRF mixins that wire the platform's tenant scoping into views.

The mixins in this module wrap the common boilerplate that every
authenticated, multi-tenant view needs: fetching the ``TenantContext`` from
the request, enforcing role/branch membership, and providing a single
``get_tenant()`` accessor that caches the result per request.

The goal is to keep business views focused on business logic. Authentication
and tenant scoping are infrastructure concerns, declared once in the view
class and reused everywhere.
"""
from __future__ import annotations

from typing import Any, ClassVar

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.tenancy.access import TenantContext, tenant_context


class TenantAPIView(APIView):
    """Base view that injects a ``TenantContext`` for the active request.

    Subclasses can declare ``required_roles`` (a tuple of role codes) to
    enforce a role check before the view method runs. The cached tenant is
    exposed via :meth:`get_tenant`. The default ``permission_classes`` is
    ``[IsAuthenticated]``; override it for public views (login, register).

    Example::

        class CaptureSessionView(TenantAPIView):
            required_roles = ("EMPLOYEE", "OWNER", "MONITOR")

            def post(self, request):
                context = self.get_tenant()
                company = context.company
                ...
    """

    # Default to requiring authentication; public views override this.
    permission_classes: ClassVar[list[type]] = [IsAuthenticated]

    # Tuple of acceptable roles. Empty tuple means "no role restriction beyond
    # authentication". The check fires lazily inside ``get_tenant`` so it does
    # not affect views that opt out of the contract (e.g. internal-only
    # endpoints that already have their own guard). The element type is
    # Runtime role constants come from Django ``TextChoices``. Mypy sees those
    # members as their declaration tuples without django-stubs, so normalize
    # them when enforcing access instead of pushing casts into every view.
    required_roles: ClassVar[tuple[Any, ...]] = ()

    def get_tenant(self) -> TenantContext:
        """Return the cached :class:`TenantContext` for the current request.

        The first call materialises the context (which may raise
        :class:`PlatformPermissionException` for anonymous users or
        cross-tenant access). Subsequent calls during the same request reuse
        the cached value to avoid duplicate database hits.
        """
        request = self.request
        cached: TenantContext | None = getattr(request, "_cached_tenant", None)
        if cached is not None:
            return cached
        context = tenant_context(request)
        if self.required_roles:
            context.require_roles(*(str(role) for role in self.required_roles))
        request._cached_tenant = context
        return context


__all__: list[Any] = ["TenantAPIView"]
