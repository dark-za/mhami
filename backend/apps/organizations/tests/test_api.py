from __future__ import annotations

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def _provision(client: Client):
    from django.core.management import call_command

    call_command(
        "provision_owner",
        organization_name="Acme",
        owner_login_id="owner2",
        owner_display_name="Owner2",
        password="Mha!mi-Test-2026#",
    )
    from apps.identity.models import User

    owner = User.objects.get(login_id="owner2")
    client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner2", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    return owner


def test_create_branch_and_weekly_shift():
    client = Client()
    owner = _provision(client)
    owner_id = str(owner.id)
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
