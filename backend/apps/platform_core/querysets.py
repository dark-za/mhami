"""Tenant-aware QuerySet + Manager for company-scoped models.

The platform isolates every business record behind a :class:`Company` foreign
key. This module gives those models a uniform :class:`TenantManager` whose
queryset exposes ``for_company()`` and ``for_company_and_branches()`` so
views and services never have to write ``.filter(company=...)`` by hand.

Adoption is incremental: models that opt in keep their default manager
(``models.Manager()``) as a fallback so existing code keeps working, but
gain ``TenantManager`` as ``objects``. New views should prefer the typed
methods; legacy code can migrate one callsite at a time.

Example::

    class EvidenceItem(models.Model):
        company = models.ForeignKey(Company, on_delete=models.CASCADE)
        objects = TenantManager()

    # In a view:
    EvidenceItem.objects.for_company(company)
    EvidenceItem.objects.for_company_and_branches(company, branch_ids)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from uuid import UUID

    from apps.tenancy.models import Company


class TenantQuerySet(models.QuerySet):
    """QuerySet that knows how to scope to a single tenant (and optional branches)."""

    def for_company(self, company: "Company | UUID") -> "TenantQuerySet":
        """Restrict the queryset to the given company (or company id)."""
        if hasattr(company, "id"):
            return self.filter(company_id=company.id)
        return self.filter(company_id=company)

    def for_company_and_branches(
        self,
        company: "Company | UUID",
        branch_ids: "list[UUID | str] | None",
    ) -> "TenantQuerySet":
        """Restrict to ``company`` and the given branch ids (or all branches)."""
        if hasattr(company, "id"):
            company_id = company.id
        else:
            company_id = company
        if not branch_ids:
            return self.filter(company_id=company_id)
        return self.filter(company_id=company_id, branch_id__in=branch_ids)

    def for_active_company(self, company: "Company") -> "TenantQuerySet":
        """Restrict to a company whose status is in the operational set.

        Operational statuses are :attr:`CompanyStatus.TRIAL` and
        :attr:`CompanyStatus.ACTIVE`. Use this when the read path should hide
        ``read_only`` and ``pending_deletion`` tenants.
        """
        from apps.tenancy.models import CompanyStatus

        return self.for_company(company).filter(
            company__status__in=(CompanyStatus.TRIAL, CompanyStatus.ACTIVE),
        )


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):  # type: ignore[misc]
    """Default manager that exposes the :class:`TenantQuerySet` API.

    Models opt in by assigning ``objects = TenantManager()``. The manager
    inherits all standard Django queryset methods (``.filter()``,
    ``.exclude()``, etc.) so existing callsites keep working while new code
    can use ``.for_company()`` for clarity.
    """


__all__ = ["TenantManager", "TenantQuerySet"]
