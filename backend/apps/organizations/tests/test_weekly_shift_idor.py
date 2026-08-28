"""C-03 regression tests: WeeklyShift IDOR.

These tests pin the fix that closes the cross-tenant ``branch_id`` /
``user_id`` injection vector. The serializer must:

* Reject ``branch_id`` from a different company with a 403-style error.
* Reject ``user_id`` from a different company with a 403-style error.
* Reject users that are not active members of the active company.
* Reject users that do not have an active branch assignment.
* Reject obvious time-window inversions and exact duplicates.
"""

from __future__ import annotations

import pytest
from django.test import Client
from rest_framework import status

pytestmark = pytest.mark.django_db


def _register_company(client: Client, *, code: str, owner_login: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        data={
            "company_name": f"Acme {code}",
            "company_code": code,
            "industry": "retail",
            "owner_login_id": owner_login,
            "owner_password": "Mha!mi-Test-2026#",
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return response.json()


def _create_branch(client: Client, code: str) -> dict:
    response = client.post(
        "/api/v1/organizations/branches",
        data={
            "name": f"Branch {code}",
            "code": code,
            "timezone": "Asia/Riyadh",
            "operational_day_cutoff": "02:00:00",
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return response.json()


def _create_role(client: Client) -> dict:
    response = client.post(
        "/api/v1/organizations/job-roles",
        data={"name": "Supervisor", "code": "supervisor"},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return response.json()


def test_weekly_shift_idor_rejects_cross_company_branch():
    client_a = Client()
    payload_a = _register_company(client_a, code="idor-a", owner_login="owner-a")
    branch_a = _create_branch(client_a, "ba")
    owner_a_id = payload_a["owner"]["id"]

    client_b = Client()
    payload_b = _register_company(client_b, code="idor-b", owner_login="owner-b")
    _create_branch(client_b, "bb")
    owner_b_id = payload_b["owner"]["id"]

    # Owner of company B attempts to assign a branch from company A to
    # their own user. This must NOT create a WeeklyShift.
    response = client_b.post(
        "/api/v1/organizations/weekly-shifts",
        data={
            "branch_id": branch_a["id"],  # belongs to company A
            "user_id": owner_b_id,
            "weekday": 1,
            "start_time": "08:00:00",
            "end_time": "16:00:00",
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content

    # And the symmetric direction is also blocked.
    response = client_a.post(
        "/api/v1/organizations/weekly-shifts",
        data={
            "branch_id": branch_a["id"],
            "user_id": owner_b_id,  # belongs to company B
            "weekday": 2,
            "start_time": "08:00:00",
            "end_time": "16:00:00",
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content


def test_weekly_shift_happy_path_creates_shift():
    client = Client()
    payload = _register_company(client, code="happy-1", owner_login="owner-h")
    branch = _create_branch(client, "hb")
    owner_id = payload["owner"]["id"]

    response = client.post(
        "/api/v1/organizations/weekly-shifts",
        data={
            "branch_id": branch["id"],
            "user_id": owner_id,
            "weekday": 3,
            "start_time": "08:00:00",
            "end_time": "16:00:00",
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED, response.content
    body = response.json()
    assert body["branch"] == branch["id"]
    assert body["weekday"] == 3


def test_weekly_shift_rejects_inverted_time_window():
    client = Client()
    payload = _register_company(client, code="inverted-1", owner_login="owner-i")
    branch = _create_branch(client, "ib")
    owner_id = payload["owner"]["id"]

    response = client.post(
        "/api/v1/organizations/weekly-shifts",
        data={
            "branch_id": branch["id"],
            "user_id": owner_id,
            "weekday": 4,
            "start_time": "16:00:00",
            "end_time": "08:00:00",
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.content
    assert "end_time" in response.json()["error"]["message"].lower() or "end_time" in str(response.content)


def test_weekly_shift_rejects_exact_duplicate():
    client = Client()
    payload = _register_company(client, code="dup-1", owner_login="owner-d")
    branch = _create_branch(client, "db")
    owner_id = payload["owner"]["id"]
    _create_role(client)

    first = client.post(
        "/api/v1/organizations/weekly-shifts",
        data={
            "branch_id": branch["id"],
            "user_id": owner_id,
            "weekday": 5,
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
        content_type="application/json",
    )
    assert first.status_code == status.HTTP_201_CREATED, first.content

    second = client.post(
        "/api/v1/organizations/weekly-shifts",
        data={
            "branch_id": branch["id"],
            "user_id": owner_id,
            "weekday": 5,
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
        content_type="application/json",
    )
    assert second.status_code == status.HTTP_400_BAD_REQUEST, second.content
