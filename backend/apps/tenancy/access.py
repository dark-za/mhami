from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type, TypeVar
from uuid import UUID

from django.db.models import Model
from django.http import HttpRequest

from apps.organizations.models import CompanyMembership, CompanyRole, UserBranchMembership
from apps.platform_core.errors import PlatformPermissionException

from .models import Company
from .services import current_support_authorization

_T = TypeVar("_T", bound=Model)


def validate_company_reference(
    company: Company,
    model: Type[_T],
    pk: Any,
    field_name: str = "id",
    *,
    extra_filters: dict[str, Any] | None = None,
) -> _T:
    """Return a model instance that belongs to ``company`` or raise.

    BE-02: This is the single source of truth for cross-tenant reference
    validation on every serializer that takes an external ID. It enforces
    that the referenced record lives inside the active company by
    filtering on both the primary key and the company FK. The
    ``extra_filters`` parameter lets callers narrow the lookup further
    (e.g. ``active=True``) without re-implementing the helper.

    The function deliberately raises ``PlatformPermissionException`` (a
    403 in the API layer) rather than a 404 so that an IDOR probe does
    not reveal whether a record exists in another tenant.
    """
    filters: dict[str, Any] = {field_name: pk, "company": company}
    if extra_filters:
        filters.update(extra_filters)
    instance = model.objects.filter(**filters).first()
    if instance is None:
        raise PlatformPermissionException(
            f"Referenced {model.__name__} is outside the active company."
        )
    return instance


def validate_company_reference_or_none(
    company: Company,
    model: Type[_T],
    pk: Any,
    field_name: str = "id",
    *,
    extra_filters: dict[str, Any] | None = None,
) -> _T | None:
    """Variant of :func:`validate_company_reference` that returns ``None`` instead of raising.

    Useful for optional fields (e.g. ``reply_to_id`` on a discussion
    message) where the caller wants the validation to remain in sync with
    the strict variant but needs to handle the absent case themselves.
    """
    if pk in (None, ""):
        return None
    return validate_company_reference(
        company, model, pk, field_name, extra_filters=extra_filters
    )


# C-08: shared helpers for active-membership predicates that honour
# ``active_until``. Callers should prefer these helpers over a local
# ``active=True`` filter so the same boundary semantics apply everywhere.
from datetime import datetime  # noqa: E402  (kept near the helpers for readability)

from django.db.models import Q  # noqa: E402
from django.utils import timezone  # noqa: E402


def _is_active_at(value: datetime | None, *, now: datetime | None = None) -> bool:
    """Return ``True`` if ``value`` is unset or strictly in the future.

    C-08: the previous implementation only checked ``active=True`` so
    expired memberships kept their privileges until an operator manually
    flipped the boolean. This predicate is the single source of truth for
    the boundary check.
    """
    if value is None:
        return True
    comparison = now or timezone.now()
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.utc)
    return value > comparison


def active_membership_q() -> Q:
    """Return a Django ``Q`` that selects currently-active memberships.

    Use as ``Model.objects.filter(active_membership_q())`` to combine
    the boolean flag and the ``active_until`` predicate in a single
    clause. The exported helper keeps the predicate co-located with the
    rest of the tenancy primitives.
    """
    return Q(active_until__isnull=True) | Q(active_until__gt=timezone.now())


@dataclass(frozen=True)
class TenantContext:
    company: Company
    role: str | None
    branch_ids: frozenset[UUID]
    is_support: bool = False

    def require_roles(self, *roles: str) -> None:
        if self.role not in roles:
            raise PlatformPermissionException("This role cannot perform the requested action.")

    def require_branch(self, branch_id: UUID | None) -> None:
        if branch_id is not None and branch_id not in self.branch_ids:
            raise PlatformPermissionException("This branch is outside your access scope.")


def tenant_context(request: HttpRequest) -> TenantContext:
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        raise PlatformPermissionException("Authentication is required.")
    # C-08: a disabled user must not retain their session privileges even
    # if a cookie is still present.
    if not getattr(user, "is_active", True):
        raise PlatformPermissionException("This user account is disabled.")

    company_id = request.session.get("company_id")
    if not company_id:
        raise PlatformPermissionException("No active company is selected.")

    company = Company.objects.filter(id=company_id).first()
    if company is None:
        raise PlatformPermissionException("The active company is unavailable.")

    now = timezone.now()
    membership = (
        CompanyMembership.objects.filter(
            company=company,
            user=user,
            active=True,
        )
        .filter(active_membership_q())
        .only("role", "active_until")
        .first()
    )
    is_owner = company.owner_id == user.id
    support_grant = None if membership or is_owner else current_support_authorization(company, user)
    if membership is None and not is_owner and support_grant is None:
        raise PlatformPermissionException("You are not authorized for the active company.")
    # C-08: respect the support grant's own expiry in addition to the
    # ``active`` flag inside ``current_support_authorization``.
    if support_grant is not None and not _is_active_at(support_grant.expires_at, now=now):
        support_grant = None

    role = str(CompanyRole.OWNER) if is_owner else membership.role if membership else None
    if role in {CompanyRole.OWNER, CompanyRole.MONITOR} or support_grant is not None:
        branch_ids = frozenset(company.branches.filter(active=True).values_list("id", flat=True))
    else:
        branch_ids = frozenset(
            UserBranchMembership.objects.filter(
                company=company,
                user=user,
                active=True,
                branch__active=True,
            )
            .filter(active_membership_q())
            .values_list("branch_id", flat=True)
        )

    return TenantContext(
        company=company,
        role=role,
        branch_ids=branch_ids,
        is_support=support_grant is not None,
    )


def require_company_user(context: TenantContext, user_id: UUID) -> None:
    if context.company.owner_id == user_id:
        return
    if not CompanyMembership.objects.filter(
        company=context.company,
        user_id=user_id,
        active=True,
    ).filter(active_membership_q()).exists():
        raise PlatformPermissionException("The selected user is outside the active company.")
