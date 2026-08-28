from __future__ import annotations

from datetime import datetime, time

import pytest
from django.utils import timezone

from apps.organizations.models import CompanyRole
from apps.tasks.services import schedule_due_tasks



pytestmark = pytest.mark.django_db


def _context(
    make_user,
    make_company,
    make_membership,
    make_branch,
    make_template,
    make_template_version,
    make_schedule,
):
    """Set up owner+monitor with assigned branches and one scheduled task."""
    owner = make_user(login_id="export-owner", display_name="Owner")
    monitor = make_user(login_id="export-monitor", display_name="Monitor")
    company = make_company(name="Export Co", code="export-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, code="main", name="Main")
    template = make_template(company=company, branch=branch, assigned_user=owner)
    make_template_version(template=template)
    make_schedule(company=company, branch=branch, template=template, scheduled_time=time(9, 0))
    schedule_due_tasks(moment=timezone.make_aware(datetime(2026, 1, 5, 9, 30)))
    return owner, monitor, company, branch


def test_export_request_and_download(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule, force_login_company,
):
    owner, _monitor, company, branch = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    client = force_login_company(owner, company)

    response = client.post(
        "/api/v1/exports/requests",
        data={"export_type": "csv", "branch_ids": [str(branch.id)], "categories": ["tasks"]},
        content_type="application/json",
    )
    assert response.status_code == 201
    token = response.json()["download_token"]

    download = client.get(f"/api/v1/exports/download/{token}")
    assert download.status_code == 200


def test_monitor_cannot_export_unassigned_branch(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule, force_login_company,
):
    _owner, monitor, company, _branch = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    other_branch = make_branch(company=company, code="other", name="Other")
    client = force_login_company(monitor, company)

    response = client.post(
        "/api/v1/exports/requests",
        data={"export_type": "csv", "branch_ids": [str(other_branch.id)], "categories": ["tasks"]},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_monitor_can_request_export_for_assigned_branch(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule, force_login_company,
):
    _owner, monitor, company, branch = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    client = force_login_company(monitor, company)

    response = client.post(
        "/api/v1/exports/requests",
        data={"export_type": "csv", "branch_ids": [str(branch.id)], "categories": ["tasks"]},
        content_type="application/json",
    )
    assert response.status_code == 201
