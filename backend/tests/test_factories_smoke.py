"""Smoke tests for the root ``conftest.py`` factories.

These tests exist purely to verify the factories produce valid instances. The
rest of the suite will eventually adopt them; until then these tests are the
authoritative contract for what each factory accepts.
"""

from __future__ import annotations

import pytest

from apps.identity.models import User
from apps.organizations.models import Branch, CompanyMembership, CompanyRole
from apps.tenancy.models import Company, CompanyStatus

pytestmark = pytest.mark.django_db


def test_make_user_returns_user_with_login_id(make_user):
    user = make_user(login_id="alice")
    assert isinstance(user, User)
    assert user.login_id == "alice"
    assert user.check_password("TestPass123!")
    assert user.display_name == "Test User"


def test_make_user_auto_increments_login_id(make_user):
    first = make_user()
    second = make_user()
    assert first.login_id != second.login_id


def test_make_company_creates_owner_user(make_user, make_company):
    company = make_company(code="acme", industry="retail")
    assert isinstance(company, Company)
    assert company.code == "acme"
    assert company.industry == "retail"
    assert company.status == CompanyStatus.ACTIVE
    assert company.owner_id is not None
    assert company.owner.login_id.startswith("owner-")


def test_make_company_reuses_existing_owner(make_user, make_company):
    owner = make_user(login_id="boss")
    company = make_company(owner=owner, code="reuse")
    assert company.owner == owner


def test_make_branch_creates_branch_under_company(make_company, make_branch):
    company = make_company(code="branch-co")
    branch = make_branch(company=company, code="b-1", name="Main")
    assert isinstance(branch, Branch)
    assert branch.company == company
    assert branch.code == "b-1"
    assert branch.timezone == "UTC"


def test_make_membership_defaults_to_owner_role(make_user, make_company, make_membership):
    user = make_user(login_id="member-user")
    company = make_company(code="member-co")
    membership = make_membership(user=user, company=company)
    assert isinstance(membership, CompanyMembership)
    assert membership.role == CompanyRole.OWNER
    assert membership.active is True


def test_force_login_company_creates_authenticated_client(
    make_user, make_company, force_login_company
):
    owner = make_user(login_id="auth-user")
    company = make_company(owner=owner, code="auth-co")
    client = force_login_company(owner, company)
    assert client.session.get("company_id") == str(company.id)
