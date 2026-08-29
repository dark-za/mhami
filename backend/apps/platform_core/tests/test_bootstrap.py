from __future__ import annotations

from django.test import Client
from django.utils import timezone

from datetime import timedelta

from apps.organizations.models import CompanyRole


def test_bootstrap_endpoint_returns_foundation_payload():
    response = Client().get("/api/v1/bootstrap")
    assert response.status_code == 200
    payload = response.json()
    assert payload["current_user"]["is_authenticated"] is False
    assert payload["current_user"].get("role") is None
    assert payload["permissions"] == []
    assert payload["branch_scope"] == []
    assert "dashboard" in payload["enabled_modules"]


def test_bootstrap_returns_role_permissions_and_branch_scope(
    force_login_company,
    make_branch,
    make_branch_membership,
    make_company,
    make_job_role,
    make_membership,
    make_user,
):
    owner = make_user(login_id="bootstrap-owner")
    employee = make_user(login_id="bootstrap-employee")
    company = make_company(code="bootstrap-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="visible")
    other_branch = make_branch(company=company, code="hidden")
    role = make_job_role(company=company, code="staff")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role)

    owner_payload = force_login_company(owner, company).get("/api/v1/bootstrap").json()
    employee_payload = force_login_company(employee, company).get("/api/v1/bootstrap").json()

    assert owner_payload["current_user"]["role"] == "owner"
    assert "users.manage" in owner_payload["permissions"]
    assert {item["id"] for item in owner_payload["branch_scope"]} == {
        str(branch.id),
        str(other_branch.id),
    }
    assert employee_payload["current_user"]["role"] == "employee"
    assert "evidence.submit" in employee_payload["permissions"]
    assert "users.manage" not in employee_payload["permissions"]
    assert [item["id"] for item in employee_payload["branch_scope"]] == [str(branch.id)]


def test_bootstrap_branch_scope_is_display_only_not_authorization(
    force_login_company,
    make_branch,
    make_branch_membership,
    make_company,
    make_job_role,
    make_membership,
    make_template,
    make_template_version,
    make_user,
):
    owner = make_user(login_id="scope-owner")
    employee = make_user(login_id="scope-employee")
    company = make_company(code="scope-bootstrap", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    allowed_branch = make_branch(company=company, code="allowed")
    blocked_branch = make_branch(company=company, code="blocked")
    job_role = make_job_role(company=company, code="scope-staff")
    branch_membership = make_branch_membership(
        company=company,
        user=employee,
        branch=allowed_branch,
        job_role=job_role,
        active_until=timezone.now() + timedelta(days=1),
    )
    template = make_template(company=company, branch=blocked_branch, assigned_user=employee)
    make_template_version(template=template)

    client = force_login_company(employee, company)
    assert [item["code"] for item in client.get("/api/v1/bootstrap").json()["branch_scope"]] == ["allowed"]
    branch_membership.branch = blocked_branch
    branch_membership.active_until = timezone.now() - timedelta(seconds=1)
    branch_membership.save(update_fields=["branch", "active_until"])

    response = client.post(
        "/api/v1/tasks/templates",
        data={
            "company_id": str(company.id),
            "branch_id": str(blocked_branch.id),
            "slug": "stale-bootstrap",
            "name": "Stale bootstrap",
            "assignment_mode": "named_user",
        },
        content_type="application/json",
    )

    assert response.status_code == 403
