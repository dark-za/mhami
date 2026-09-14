"""Focused tests for least-privilege branch/member scoping (tasks 1-3).

Covers:
- BranchesView filtering via TenantContext.branch_ids
- bootstrap `branches` vs `branch_scope` display rule
- CompanyMembersView monitor scoping without roster leak
"""
from __future__ import annotations

import pytest
from django.utils import timezone
from datetime import timedelta

from apps.organizations.models import CompanyMembership, CompanyRole, UserBranchMembership

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# 1. Branch listing (organizations/api/views.py)
# ---------------------------------------------------------------------------

def test_branch_listing_owner_sees_all_including_inactive(force_login_company, make_user, make_company, make_branch, make_membership):
    owner = make_user(login_id="b-owner-all")
    company = make_company(owner=owner, code="b-scope-owner-all")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    active_branch = make_branch(company=company, code="active-a", active=True)
    inactive_branch = make_branch(company=company, code="inactive-a", active=False)
    client = force_login_company(owner, company)
    resp = client.get("/api/v1/organizations/branches")
    assert resp.status_code == 200
    ids = {b["id"] for b in resp.json()["branches"]}
    assert str(active_branch.id) in ids
    assert str(inactive_branch.id) in ids


def test_branch_listing_monitor_sees_only_assigned_active(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="b-owner-mon")
    company = make_company(owner=owner, code="b-scope-mon")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="b-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch_allowed = make_branch(company=company, code="allowed-mon", active=True)
    branch_hidden = make_branch(company=company, code="hidden-mon", active=True)
    branch_inactive = make_branch(company=company, code="inactive-mon", active=False)
    role = make_job_role(company=company, code="jr-mon")
    make_branch_membership(company=company, user=monitor, branch=branch_allowed, job_role=role)
    # give monitor hidden inactive assignment also (should not grant visibility since branch inactive)
    # Even if created, tenant_context filters branch__active=True so it won't appear in branch_ids.
    # We still create it to prove endpoint respects active flag.
    # Use inactive branch membership - branch inactive, so branch_ids excludes it.
    try:
        make_branch_membership(company=company, user=monitor, branch=branch_inactive, job_role=role)
    except Exception:
        pass

    client = force_login_company(monitor, company)
    resp = client.get("/api/v1/organizations/branches")
    assert resp.status_code == 200
    ids = {b["id"] for b in resp.json()["branches"]}
    assert str(branch_allowed.id) in ids
    assert str(branch_hidden.id) not in ids
    assert str(branch_inactive.id) not in ids
    # Must not receive inactive branches even if assigned
    for b in resp.json()["branches"]:
        assert b["active"] is True


def test_branch_listing_employee_sees_only_assigned_active(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="b-owner-emp")
    company = make_company(owner=owner, code="b-scope-emp")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="b-employee")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch_allowed = make_branch(company=company, code="emp-allowed", active=True)
    branch_hidden = make_branch(company=company, code="emp-hidden", active=True)
    role = make_job_role(company=company, code="jr-emp")
    make_branch_membership(company=company, user=employee, branch=branch_allowed, job_role=role)

    client = force_login_company(employee, company)
    resp = client.get("/api/v1/organizations/branches")
    assert resp.status_code == 200
    ids = {b["id"] for b in resp.json()["branches"]}
    assert str(branch_allowed.id) in ids
    assert str(branch_hidden.id) not in ids


def test_branch_listing_monitor_with_no_assignment_sees_empty(force_login_company, make_user, make_company, make_branch, make_membership):
    owner = make_user(login_id="b-owner-noassign")
    company = make_company(owner=owner, code="b-noassign")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="b-monitor-empty")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    make_branch(company=company, code="orphan", active=True)
    client = force_login_company(monitor, company)
    resp = client.get("/api/v1/organizations/branches")
    assert resp.status_code == 200
    assert resp.json()["branches"] == []


def test_branch_listing_expired_membership_not_visible(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="b-owner-exp")
    company = make_company(owner=owner, code="b-exp")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="b-emp-exp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="exp-branch", active=True)
    role = make_job_role(company=company, code="jr-exp")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role, active_until=timezone.now() - timedelta(seconds=10))

    client = force_login_company(employee, company)
    resp = client.get("/api/v1/organizations/branches")
    assert resp.status_code == 200
    assert resp.json()["branches"] == []


# ---------------------------------------------------------------------------
# 2. Bootstrap branches scoping (platform_core/services.py)
# ---------------------------------------------------------------------------

def test_bootstrap_branches_owner_gets_all_active(force_login_company, make_user, make_company, make_branch, make_membership):
    owner = make_user(login_id="bs-owner")
    company = make_company(owner=owner, code="bs-owner-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    b1 = make_branch(company=company, code="bs-a", active=True)
    b2 = make_branch(company=company, code="bs-b", active=True)
    make_branch(company=company, code="bs-inactive", active=False)
    payload = force_login_company(owner, company).get("/api/v1/bootstrap").json()
    ids = {b["id"] for b in payload["branches"]}
    assert str(b1.id) in ids
    assert str(b2.id) in ids
    # inactive not present
    assert all(b["active"] is True for b in payload["branches"])
    # branch_scope for owner equals all active (same as branches)
    scope_ids = {b["id"] for b in payload["branch_scope"]}
    assert scope_ids == ids


def test_bootstrap_branches_monitor_scoped_and_branch_scope_equal(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="bs-owner2")
    company = make_company(owner=owner, code="bs-mon-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="bs-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    allowed = make_branch(company=company, code="bs-allowed", active=True)
    hidden = make_branch(company=company, code="bs-hidden", active=True)
    role = make_job_role(company=company, code="bs-jr")
    make_branch_membership(company=company, user=monitor, branch=allowed, job_role=role)

    payload = force_login_company(monitor, company).get("/api/v1/bootstrap").json()
    branch_ids = {b["id"] for b in payload["branches"]}
    scope_ids = {b["id"] for b in payload["branch_scope"]}
    assert branch_ids == {str(allowed.id)}
    assert scope_ids == {str(allowed.id)}
    assert str(hidden.id) not in branch_ids
    assert branch_ids == scope_ids


def test_bootstrap_branches_employee_scoped(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="bs-owner3")
    company = make_company(owner=owner, code="bs-emp-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="bs-employee")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    allowed = make_branch(company=company, code="bs-emp-allowed", active=True)
    make_branch(company=company, code="bs-emp-hidden", active=True)
    role = make_job_role(company=company, code="bs-jr2")
    make_branch_membership(company=company, user=employee, branch=allowed, job_role=role)

    payload = force_login_company(employee, company).get("/api/v1/bootstrap").json()
    assert {b["id"] for b in payload["branches"]} == {str(allowed.id)}
    assert {b["id"] for b in payload["branch_scope"]} == {str(allowed.id)}


def test_bootstrap_branches_expired_assignment_empty(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="bs-owner-exp")
    company = make_company(owner=owner, code="bs-exp-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="bs-emp-exp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="bs-exp-branch", active=True)
    role = make_job_role(company=company, code="bs-jr-exp")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role, active_until=timezone.now() - timedelta(seconds=5))
    payload = force_login_company(employee, company).get("/api/v1/bootstrap").json()
    assert payload["branches"] == []
    assert payload["branch_scope"] == []


# ---------------------------------------------------------------------------
# 3. CompanyMembersView monitor scoping (tenancy/api/views.py)
# ---------------------------------------------------------------------------

def test_company_members_owner_sees_all(force_login_company, make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership):
    owner = make_user(login_id="mem-owner")
    company = make_company(owner=owner, code="mem-owner-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="mem-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    emp_in = make_user(login_id="mem-emp-in")
    make_membership(user=emp_in, company=company, role=CompanyRole.EMPLOYEE)
    emp_out = make_user(login_id="mem-emp-out")
    make_membership(user=emp_out, company=company, role=CompanyRole.EMPLOYEE)
    branch_a = make_branch(company=company, code="mem-a")
    branch_b = make_branch(company=company, code="mem-b")
    role = make_job_role(company=company, code="mem-jr")
    make_branch_membership(company=company, user=emp_in, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=emp_out, branch=branch_b, job_role=role)
    make_branch_membership(company=company, user=monitor, branch=branch_a, job_role=role)

    client = force_login_company(owner, company)
    resp = client.get("/api/v1/auth/company/members")
    assert resp.status_code == 200
    returned = {m["user_id"] for m in resp.json()["memberships"]}
    assert str(owner.id) in returned
    assert str(monitor.id) in returned
    assert str(emp_in.id) in returned
    assert str(emp_out.id) in returned


def test_company_members_monitor_only_employees_in_branch_scope(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="mem2-owner")
    company = make_company(owner=owner, code="mem2-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="mem2-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    other_monitor = make_user(login_id="mem2-monitor2")
    make_membership(user=other_monitor, company=company, role=CompanyRole.MONITOR)

    emp_in = make_user(login_id="mem2-emp-in")
    make_membership(user=emp_in, company=company, role=CompanyRole.EMPLOYEE)
    emp_out = make_user(login_id="mem2-emp-out")
    make_membership(user=emp_out, company=company, role=CompanyRole.EMPLOYEE)

    branch_a = make_branch(company=company, code="mem2-a")
    branch_b = make_branch(company=company, code="mem2-b")
    role = make_job_role(company=company, code="mem2-jr")
    make_branch_membership(company=company, user=monitor, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=emp_in, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=emp_out, branch=branch_b, job_role=role)
    make_branch_membership(company=company, user=other_monitor, branch=branch_a, job_role=role)

    client = force_login_company(monitor, company)
    resp = client.get("/api/v1/auth/company/members")
    assert resp.status_code == 200
    returned_ids = {m["user_id"] for m in resp.json()["memberships"]}
    returned_roles = {m["role"] for m in resp.json()["memberships"]}
    # only emp_in visible
    assert str(emp_in.id) in returned_ids
    assert str(emp_out.id) not in returned_ids
    assert str(owner.id) not in returned_ids
    assert str(monitor.id) not in returned_ids
    assert str(other_monitor.id) not in returned_ids
    assert returned_roles == {"employee"} or returned_roles == {CompanyRole.EMPLOYEE}


def test_company_members_monitor_excludes_inactive_employee_and_branch(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="mem3-owner")
    company = make_company(owner=owner, code="mem3-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="mem3-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    emp_active = make_user(login_id="mem3-emp-active")
    make_membership(user=emp_active, company=company, role=CompanyRole.EMPLOYEE)
    emp_inactive_membership = make_user(login_id="mem3-emp-inactive")
    make_membership(user=emp_inactive_membership, company=company, role=CompanyRole.EMPLOYEE, active=False)
    emp_inactive_branch = make_user(login_id="mem3-emp-branch-inactive")
    make_membership(user=emp_inactive_branch, company=company, role=CompanyRole.EMPLOYEE)
    emp_expired_branch = make_user(login_id="mem3-emp-expired")
    make_membership(user=emp_expired_branch, company=company, role=CompanyRole.EMPLOYEE)

    branch = make_branch(company=company, code="mem3-branch", active=True)
    inactive_branch = make_branch(company=company, code="mem3-inactive-branch", active=False)
    role = make_job_role(company=company, code="mem3-jr")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)
    make_branch_membership(company=company, user=emp_active, branch=branch, job_role=role)
    make_branch_membership(company=company, user=emp_inactive_branch, branch=branch, job_role=role, active=False)
    make_branch_membership(company=company, user=emp_expired_branch, branch=branch, job_role=role, active_until=timezone.now() - timedelta(days=1))
    # emp on inactive branch
    emp_on_inactive_branch = make_user(login_id="mem3-emp-on-inactive")
    make_membership(user=emp_on_inactive_branch, company=company, role=CompanyRole.EMPLOYEE)
    make_branch_membership(company=company, user=emp_on_inactive_branch, branch=inactive_branch, job_role=role)
    # also give monitor membership to inactive branch to test inactive branch not granting scope (monitor already has active branch)
    # monitor scope is branch (active). emp_on_inactive_branch should not be visible even though both have "a branch" but not overlapping active scope.

    client = force_login_company(monitor, company)
    resp = client.get("/api/v1/auth/company/members")
    assert resp.status_code == 200
    ids = {m["user_id"] for m in resp.json()["memberships"]}
    assert str(emp_active.id) in ids
    assert str(emp_inactive_membership.id) not in ids
    assert str(emp_inactive_branch.id) not in ids
    assert str(emp_expired_branch.id) not in ids
    assert str(emp_on_inactive_branch.id) not in ids


def test_company_members_monitor_no_scope_empty(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="mem4-owner")
    company = make_company(owner=owner, code="mem4-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="mem4-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    emp = make_user(login_id="mem4-emp")
    make_membership(user=emp, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="mem4-branch")
    role = make_job_role(company=company, code="mem4-jr")
    make_branch_membership(company=company, user=emp, branch=branch, job_role=role)
    # monitor has no branch assignment

    client = force_login_company(monitor, company)
    resp = client.get("/api/v1/auth/company/members")
    assert resp.status_code == 200
    assert resp.json()["memberships"] == []


def test_company_members_employee_forbidden(force_login_company, make_user, make_company, make_membership):
    owner = make_user(login_id="mem5-owner")
    company = make_company(owner=owner, code="mem5-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="mem5-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    client = force_login_company(employee, company)
    resp = client.get("/api/v1/auth/company/members")
    assert resp.status_code == 403


def test_company_members_monitor_multiple_branches_union(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="mem6-owner")
    company = make_company(owner=owner, code="mem6-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="mem6-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    emp_a = make_user(login_id="mem6-emp-a")
    make_membership(user=emp_a, company=company, role=CompanyRole.EMPLOYEE)
    emp_b = make_user(login_id="mem6-emp-b")
    make_membership(user=emp_b, company=company, role=CompanyRole.EMPLOYEE)
    emp_c = make_user(login_id="mem6-emp-c")
    make_membership(user=emp_c, company=company, role=CompanyRole.EMPLOYEE)
    branch_a = make_branch(company=company, code="mem6-a")
    branch_b = make_branch(company=company, code="mem6-b")
    branch_c = make_branch(company=company, code="mem6-c")
    role = make_job_role(company=company, code="mem6-jr")
    make_branch_membership(company=company, user=monitor, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=monitor, branch=branch_b, job_role=role)
    make_branch_membership(company=company, user=emp_a, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=emp_b, branch=branch_b, job_role=role)
    make_branch_membership(company=company, user=emp_c, branch=branch_c, job_role=role)

    client = force_login_company(monitor, company)
    resp = client.get("/api/v1/auth/company/members")
    ids = {m["user_id"] for m in resp.json()["memberships"]}
    assert str(emp_a.id) in ids
    assert str(emp_b.id) in ids
    assert str(emp_c.id) not in ids


def test_company_members_monitor_active_until_respected(force_login_company, make_user, make_company, make_branch, make_membership, make_job_role, make_branch_membership):
    owner = make_user(login_id="mem7-owner")
    company = make_company(owner=owner, code="mem7-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="mem7-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    emp_future = make_user(login_id="mem7-emp-future")
    make_membership(user=emp_future, company=company, role=CompanyRole.EMPLOYEE, active_until=timezone.now() + timedelta(days=1))
    emp_expired = make_user(login_id="mem7-emp-exp")
    make_membership(user=emp_expired, company=company, role=CompanyRole.EMPLOYEE, active_until=timezone.now() - timedelta(days=1))
    branch = make_branch(company=company, code="mem7-branch")
    role = make_job_role(company=company, code="mem7-jr")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)
    make_branch_membership(company=company, user=emp_future, branch=branch, job_role=role)
    make_branch_membership(company=company, user=emp_expired, branch=branch, job_role=role)

    client = force_login_company(monitor, company)
    resp = client.get("/api/v1/auth/company/members")
    ids = {m["user_id"] for m in resp.json()["memberships"]}
    assert str(emp_future.id) in ids
    assert str(emp_expired.id) not in ids


def test_monitor_creates_employee_with_atomic_scoped_branch_assignment(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
):
    owner = make_user(login_id="create-owner")
    company = make_company(owner=owner, code="create-monitor-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="create-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    allowed_branch = make_branch(company=company, code="create-allowed")
    hidden_branch = make_branch(company=company, code="create-hidden")
    job_role = make_job_role(company=company, code="create-role")
    make_branch_membership(company=company, user=monitor, branch=allowed_branch, job_role=job_role)
    client = force_login_company(monitor, company)

    missing_assignment = client.post(
        "/api/v1/auth/company/users",
        data={"login_id": "new-missing", "password": "Mha!mi-Test-2026#", "role": "employee"},
        content_type="application/json",
    )
    assert missing_assignment.status_code == 403

    outside_scope = client.post(
        "/api/v1/auth/company/users",
        data={
            "login_id": "new-hidden",
            "password": "Mha!mi-Test-2026#",
            "role": "employee",
            "branch_id": str(hidden_branch.id),
            "job_role_id": str(job_role.id),
        },
        content_type="application/json",
    )
    assert outside_scope.status_code == 403

    created = client.post(
        "/api/v1/auth/company/users",
        data={
            "login_id": "new-employee",
            "password": "Mha!mi-Test-2026#",
            "role": "employee",
            "branch_id": str(allowed_branch.id),
            "job_role_id": str(job_role.id),
        },
        content_type="application/json",
    )
    assert created.status_code == 201
    user_id = created.json()["user"]["id"]
    assert CompanyMembership.objects.filter(company=company, user_id=user_id, role=CompanyRole.EMPLOYEE).exists()
    assert UserBranchMembership.objects.filter(
        company=company,
        user_id=user_id,
        branch=allowed_branch,
        job_role=job_role,
        active=True,
    ).exists()
