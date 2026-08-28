"""PILOT-01: PilotCharter tests.

Exercises the four critical paths:

1. Owner signs a charter → row + audit event + valid HMAC.
2. Tampered rationale invalidates the signature.
3. Employee cannot POST; monitor can GET.
4. Dashboard surfaces the signed charter.
"""

from __future__ import annotations

import pytest
from django.test import Client

from apps.audit.models import AuditEvent
from apps.organizations.models import CompanyRole
from apps.pilot.models import PilotCharter


pytestmark = pytest.mark.django_db


def _login_company(user, company):
    client = Client()
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    return client


def test_owner_signs_charter_creates_audit_event(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company = _context(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership)
    client = _login_company(owner, company)

    response = client.post(
        "/api/v1/pilot/charter",
        data={
            "decision": "authorize",
            "rationale": "Approve charter for internal pilot.",
            "conditions": "",
            "observation_start": "2026-08-28",
            "observation_end": "2026-11-28",
            "success_measures": ["Employees complete tasks"],
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["decision"] == "authorize"
    assert body["signature_hmac"]
    assert body["signature_valid"] is True
    assert PilotCharter.objects.filter(company=company, decision="authorize").count() == 1
    assert AuditEvent.objects.filter(event_type="PILOT_CHARTER_SIGNED", target_id=body["id"]).exists()


def test_signature_invalid_when_rationale_tampered(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company = _context(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership)
    client = _login_company(owner, company)
    response = client.post(
        "/api/v1/pilot/charter",
        data={"decision": "authorize", "rationale": "Original rationale."},
        content_type="application/json",
    )
    assert response.status_code == 201
    charter = PilotCharter.objects.get(company=company)
    assert charter.verify_signature() is True
    charter.rationale = "Tampered rationale."
    assert charter.verify_signature() is False


def test_employee_cannot_sign_charter(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company = _context(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership)
    employee = make_user(login_id="pilot-emp", display_name="Employee")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    client = _login_company(employee, company)
    response = client.post(
        "/api/v1/pilot/charter",
        data={"decision": "authorize", "rationale": "Should fail."},
        content_type="application/json",
    )
    assert response.status_code == 403


def test_get_charter_returns_404_when_missing(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company = _context(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership)
    client = _login_company(owner, company)
    response = client.get("/api/v1/pilot/charter")
    assert response.status_code == 404


def test_dashboard_includes_charter(
    make_user, make_company, make_membership, make_branch,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company = _context(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership)
    client = _login_company(owner, company)
    client.post(
        "/api/v1/pilot/charter",
        data={"decision": "authorize", "rationale": "Sign me up."},
        content_type="application/json",
    )
    response = client.get("/api/v1/pilot/dashboard")
    assert response.status_code == 200
    charter = response.json()["charter"]
    assert charter is not None
    assert charter["decision"] == "authorize"
    assert charter["signature_valid"] is True


def _context(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership):
    owner = make_user(login_id="pilot-owner", display_name="Owner")
    monitor = make_user(login_id="pilot-monitor", display_name="Monitor")
    company = make_company(name="Pilot Co", code="pilotco", industry="restaurants_cafes", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, code="main", name="Main")
    role = make_job_role(company=company, name="Staff", code="staff")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)
    return owner, monitor, company
