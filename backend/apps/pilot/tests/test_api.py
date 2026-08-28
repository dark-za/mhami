from __future__ import annotations

import pytest
from django.test import Client

from apps.organizations.models import CompanyRole


pytestmark = pytest.mark.django_db


def _context(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership):
    """Build owner+monitor with one assigned branch."""
    owner = make_user(login_id="pilot-owner", display_name="Owner")
    monitor = make_user(login_id="pilot-monitor", display_name="Monitor")
    company = make_company(
        name="Pilot Co", code="pilot-co", industry="restaurants_cafes", owner=owner,
    )
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, code="main", name="Main")
    role = make_job_role(company=company, name="Staff", code="staff")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)
    return owner, monitor, company


def test_pilot_dashboard_and_weekly_report(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company = _context(
        make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership,
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    program = client.patch("/api/v1/pilot/program", data={"status": "active", "ai_provider_name": "fake"}, content_type="application/json")
    assert program.status_code == 200

    dashboard = client.get("/api/v1/pilot/dashboard")
    assert dashboard.status_code == 200

    report = client.post("/api/v1/pilot/weekly-reports", data={"week_ending": "2030-01-01", "metrics": {"tasks": 5}}, content_type="application/json")
    assert report.status_code == 201


def test_issue_resolution_and_change_approval(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company = _context(
        make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership,
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    issue = client.post("/api/v1/pilot/issues", data={"title": "Blur failing", "severity": "high"}, content_type="application/json")
    assert issue.status_code == 201
    issue_id = issue.json()["id"]

    resolved = client.patch(f"/api/v1/pilot/issues/{issue_id}", data={"status": "resolved"}, content_type="application/json")
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    change = client.post("/api/v1/pilot/change-requests", data={"title": "Extend trial", "rationale": "More branches"}, content_type="application/json")
    assert change.status_code == 201
    change_id = change.json()["id"]

    decided = client.patch(f"/api/v1/pilot/change-requests/{change_id}", data={"status": "approved"}, content_type="application/json")
    assert decided.status_code == 200
    body = decided.json()
    assert body["status"] == "approved"
    assert body["approved_by"] == str(owner.id)


def test_employee_cannot_resolve_issue(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    _owner, _monitor, company = _context(
        make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership,
    )
    employee = make_user(login_id="pilot-employee", display_name="Employee")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)

    client = Client()
    client.force_login(employee, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    issue = client.post("/api/v1/pilot/issues", data={"title": "Blocked camera"}, content_type="application/json")
    assert issue.status_code == 403
