"""H-01 / H-02 regression tests: ReviewDecision and ReviewPolicy RBAC.

These tests pin the role gates declared on the view classes. The class-level
``required_roles`` attribute is the single source of truth so any change
that removes the gate must be deliberate and code-reviewed.
"""

from __future__ import annotations

import pytest
from django.test import Client
from rest_framework import status

from apps.organizations.models import CompanyRole

pytestmark = pytest.mark.django_db


def _setup_company(make_user, make_company, make_membership, make_branch):
    owner = make_user(login_id="rbac-owner")
    monitor = make_user(login_id="rbac-monitor")
    employee = make_user(login_id="rbac-employee")
    company = make_company(code="rbac-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="r1")
    return owner, monitor, employee, company, branch


def _login(user, company):
    client = Client()
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    return client


# ---------------------------------------------------------------------------
# H-01: ReviewDecisionCreateView
# ---------------------------------------------------------------------------


def test_employee_cannot_create_review_decision(
    make_user, make_company, make_membership, make_branch,
):
    _owner, _monitor, employee, company, _branch = _setup_company(
        make_user, make_company, make_membership, make_branch,
    )
    client = _login(employee, company)
    response = client.post(
        "/api/v1/reviews/decisions",
        data={"decision_type": "approve"},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content


def test_monitor_can_create_review_decision(
    make_user, make_company, make_membership, make_branch,
):
    _owner, monitor, _employee, company, _branch = _setup_company(
        make_user, make_company, make_membership, make_branch,
    )
    client = _login(monitor, company)
    response = client.post(
        "/api/v1/reviews/decisions",
        data={"decision_type": "approve"},
        content_type="application/json",
    )
    # The service layer may still raise if there is no pending queue
    # entry, but it must not reject for lack of role. We accept either
    # 201 (happy path) or 400 (no item to decide on) — anything else is
    # an RBAC regression.
    assert response.status_code in {
        status.HTTP_201_CREATED,
        status.HTTP_400_BAD_REQUEST,
    }, response.content


def test_owner_can_create_review_decision(
    make_user, make_company, make_membership, make_branch,
):
    owner, _monitor, _employee, company, _branch = _setup_company(
        make_user, make_company, make_membership, make_branch,
    )
    client = _login(owner, company)
    response = client.post(
        "/api/v1/reviews/decisions",
        data={"decision_type": "approve"},
        content_type="application/json",
    )
    assert response.status_code in {
        status.HTTP_201_CREATED,
        status.HTTP_400_BAD_REQUEST,
    }, response.content


# ---------------------------------------------------------------------------
# H-02: ReviewPolicyView
# ---------------------------------------------------------------------------


def test_employee_cannot_patch_policy(
    make_user, make_company, make_membership, make_branch,
):
    _owner, _monitor, employee, company, _branch = _setup_company(
        make_user, make_company, make_membership, make_branch,
    )
    client = _login(employee, company)
    response = client.patch(
        "/api/v1/reviews/policy",
        data={"extra_evidence_required": True},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content


def test_monitor_cannot_patch_policy(
    make_user, make_company, make_membership, make_branch,
):
    _owner, monitor, _employee, company, _branch = _setup_company(
        make_user, make_company, make_membership, make_branch,
    )
    client = _login(monitor, company)
    response = client.patch(
        "/api/v1/reviews/policy",
        data={"extra_evidence_required": True},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content


def test_owner_can_patch_policy(
    make_user, make_company, make_membership, make_branch,
):
    owner, _monitor, _employee, company, _branch = _setup_company(
        make_user, make_company, make_membership, make_branch,
    )
    client = _login(owner, company)
    response = client.patch(
        "/api/v1/reviews/policy",
        data={"extra_evidence_required": True},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK, response.content
    assert response.json()["extra_evidence_required"] is True


def test_policy_get_does_not_require_owner(
    make_user, make_company, make_membership, make_branch,
):
    _owner, _monitor, employee, company, _branch = _setup_company(
        make_user, make_company, make_membership, make_branch,
    )
    client = _login(employee, company)
    response = client.get("/api/v1/reviews/policy")
    # The historical contract allows employees to read the policy so
    # the client can render the rules. We only locked PATCH.
    assert response.status_code == status.HTTP_200_OK, response.content
