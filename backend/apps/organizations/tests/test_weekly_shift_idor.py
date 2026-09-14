"""WeeklyShift tests adapted for single-organization self-hosted mode.

The legacy cross-company IDOR test (two separate organizations) is no longer
applicable because a deployment contains exactly one organization provisioned
via ``provision_owner``. The remaining tests verify branch/shift creation and
validation within the sole organization.
"""

from __future__ import annotations

import pytest
from django.test import Client
from rest_framework import status

pytestmark = pytest.mark.django_db


def _provision_and_login(client: Client, *, owner_login: str) -> dict:
    from django.core.management import call_command
    from apps.identity.models import User

    try:
        call_command(
            "provision_owner",
            organization_name=f"Acme {owner_login}",
            owner_login_id=owner_login,
            owner_display_name=owner_login,
            password="Mha!mi-Test-2026#",
        )
    except Exception:
        # Already provisioned in this test DB — reuse existing org
        pass
    # Ensure client is logged in
    client.post(
        "/api/v1/auth/login",
        data={"login_id": owner_login, "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    owner = User.objects.get(login_id=owner_login)
    return {"owner": {"id": str(owner.id)}}


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


def test_weekly_shift_happy_path_creates_shift():
    client = Client()
    payload = _provision_and_login(client, owner_login="owner-h")
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
    payload = _provision_and_login(client, owner_login="owner-h")
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


def test_weekly_shift_rejects_exact_duplicate():
    client = Client()
    payload = _provision_and_login(client, owner_login="owner-h")
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
