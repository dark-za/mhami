from __future__ import annotations

from datetime import datetime

import pytest
from django.utils import timezone

from freezegun import freeze_time

from apps.organizations.models import CompanyRole
from apps.tasks.models import TaskStatus
from apps.tasks.services import claim_task, complete_task, mark_overdue_tasks, request_transfer, resolve_transfer, schedule_due_tasks, start_task


pytestmark = pytest.mark.django_db


def _create_context(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner = make_user(login_id="owner-task", display_name="Owner Task")
    company = make_company(name="Task Co", code="task-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    branch = make_branch(company=company, code="main", name="Main")
    template = make_template(
        company=company, branch=branch,
        slug="opening-check", name="Opening check", assigned_user=owner,
    )
    make_template_version(
        template=template,
        instructions="Open the store",
        checklist_definition=[{"step": "unlock"}],
    )
    schedule = make_schedule(company=company, branch=branch, template=template)
    return owner, company, branch, template, schedule


@freeze_time("2026-01-05 09:30:00+00:00")
def test_scheduler_is_idempotent(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    _owner, company, _branch, _template, _schedule = _create_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    first = schedule_due_tasks()
    second = schedule_due_tasks()
    assert len(first) == 1
    assert len(second) == 1
    assert company.task_instances.count() == 1
    assert company.task_instances.first().status == TaskStatus.PENDING


@freeze_time("2026-01-05 09:30:00+00:00")
def test_claim_and_start_transitions(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner, _company, _branch, _template, _schedule = _create_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    instance = schedule_due_tasks()[0]
    claimed = claim_task(str(instance.id), owner)
    assert claimed.status == TaskStatus.CLAIMED
    started = start_task(str(instance.id), owner)
    assert started.status == TaskStatus.IN_PROGRESS
    completed = complete_task(str(instance.id), owner)
    assert completed.status == TaskStatus.COMPLETED


@freeze_time("2026-01-05 10:30:00+00:00")
def test_overdue_sweep_marks_expired_instances(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    _owner, _company, _branch, _template, _schedule = _create_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    instance = schedule_due_tasks(moment=timezone.make_aware(datetime(2026, 1, 5, 9, 30)))
    assert instance
    overdue = mark_overdue_tasks()
    assert len(overdue) == 1
    assert overdue[0].status == TaskStatus.OVERDUE


@freeze_time("2026-01-05 09:30:00+00:00")
def test_approved_transfer_reassigns_in_progress_task_to_pending(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner, _company, _branch, _template, _schedule = _create_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    other = make_user(login_id="other-transfer", display_name="Other")
    instance = schedule_due_tasks()[0]
    claim_task(str(instance.id), owner)
    started = start_task(str(instance.id), owner)
    assert started.status == TaskStatus.IN_PROGRESS
    transfer = request_transfer(str(instance.id), owner, other, "Handing over shift")
    resolved = resolve_transfer(str(transfer.id), owner, approved=True)
    instance.refresh_from_db()
    assert resolved.status == "approved"
    assert instance.status == TaskStatus.PENDING
    assert instance.assigned_user_id == other.id
