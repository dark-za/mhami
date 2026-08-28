from __future__ import annotations

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def _register(client: Client):
    return client.post(
        "/api/v1/auth/register",
        data={
            "company_name": "Acme",
            "company_code": "acme2",
            "industry": "retail",
            "owner_login_id": "owner2",
            "owner_password": "Mha!mi-Test-2026#",
        },
        content_type="application/json",
    )


def test_create_branch_and_weekly_shift():
    client = Client()
    register_response = _register(client)
    assert register_response.status_code == 201
    owner_id = register_response.json()["owner"]["id"]
    branch = client.post(
        "/api/v1/organizations/branches",
        data={
            "name": "North",
            "code": "north",
            "timezone": "Asia/Riyadh",
            "operational_day_cutoff": "02:00:00",
        },
        content_type="application/json",
    ).json()
    role = client.post(
        "/api/v1/organizations/job-roles",
        data={"name": "Supervisor", "code": "supervisor"},
        content_type="application/json",
    ).json()
    shift = client.post(
        "/api/v1/organizations/weekly-shifts",
        data={
            "branch_id": branch["id"],
            "user_id": owner_id,
            "weekday": 1,
            "start_time": "08:00:00",
            "end_time": "16:00:00",
        },
        content_type="application/json",
    )
    assert branch["code"] == "north"
    assert role["code"] == "supervisor"
    assert shift.status_code == 201
