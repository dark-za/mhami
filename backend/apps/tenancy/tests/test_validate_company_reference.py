"""BE-02 regression tests: ``validate_company_reference`` helper.

The helper is the single source of truth for cross-tenant reference
validation on every serializer that takes an external ID. It must:

* Return the matching instance when the record belongs to the active
  company.
* Raise :class:`PlatformPermissionException` when the record is from a
  different company.
* Accept additional filter criteria (e.g. ``active=True``) for records
  that have lifecycle states.
* Return ``None`` for the ``_or_none`` variant when the input is blank.
"""
from __future__ import annotations

import pytest

from apps.organizations.models import Branch
from apps.platform_core.errors import PlatformPermissionException
from apps.tenancy.access import (
    validate_company_reference,
    validate_company_reference_or_none,
)
from apps.tenancy.models import Company

pytestmark = pytest.mark.django_db


def test_validate_company_reference_returns_matching_instance(make_company, make_branch):
    company = make_company()
    branch = make_branch(company=company)
    result = validate_company_reference(company, Branch, branch.id)
    assert result.id == branch.id
    assert result.company_id == company.id


def test_validate_company_reference_rejects_cross_tenant_id(make_company, make_branch):
    company_a = make_company()
    company_b = make_company()
    branch_b = make_branch(company=company_b)
    with pytest.raises(PlatformPermissionException):
        validate_company_reference(company_a, Branch, branch_b.id)


def test_validate_company_reference_applies_extra_filters(make_company, make_branch):
    company = make_company()
    branch = make_branch(company=company, active=True)
    # ``active=False`` should miss the record and raise.
    with pytest.raises(PlatformPermissionException):
        validate_company_reference(
            company,
            Branch,
            branch.id,
            extra_filters={"active": False},
        )


def test_validate_company_reference_or_none_returns_none_for_blank(make_company):
    company = make_company()
    assert validate_company_reference_or_none(company, Branch, None) is None
    assert validate_company_reference_or_none(company, Branch, "") is None


def test_validate_company_reference_or_none_raises_for_cross_tenant(make_company, make_branch):
    company_a = make_company()
    company_b = make_company()
    branch_b = make_branch(company=company_b)
    with pytest.raises(PlatformPermissionException):
        validate_company_reference_or_none(company_a, Branch, branch_b.id)
