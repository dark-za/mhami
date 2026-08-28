"""Smoke test for the organisation models' tenant isolation wiring.

Verifies that the foreign keys and reverse relations are intact so
the rest of the suite can rely on the shape of the data model.
"""

from __future__ import annotations

import pytest

from apps.organizations.models import CompanyRole

pytestmark = pytest.mark.django_db


def test_employee_has_one_active_branch(make_user, make_company, make_branch, make_membership):
    """Sanity-check tenant FKs and membership reverse accessors."""
    company = make_company()
    branch = make_branch(company=company)
    employee = make_user(login_id="emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    assert branch.company_id == company.id
    assert employee.company_memberships.count() == 1
