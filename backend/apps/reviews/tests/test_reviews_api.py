from __future__ import annotations

from datetime import datetime, time

import pytest
from django.test import Client
from django.utils import timezone

from apps.organizations.models import CompanyRole
from apps.reviews.models import ReviewDecision
from apps.tasks.services import schedule_due_tasks


pytestmark = pytest.mark.django_db


def _task_context(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    """Build owner+monitor with two branches, one assigned to monitor, two scheduled tasks."""
    owner = make_user(login_id="review-owner", display_name="Owner")
    monitor = make_user(login_id="review-monitor", display_name="Monitor")
    company = make_company(name="Review Co", code="review-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch_one = make_branch(company=company, code="a", name="A")
    branch_two = make_branch(company=company, code="b", name="B")
    role = make_job_role(company=company, name="Staff", code="staff")
    make_branch_membership(company=company, user=monitor, branch=branch_one, job_role=role)

    template_one = make_template(
        company=company, branch=branch_one,
        slug="daily", name="Daily", assigned_user=owner,
    )
    make_template_version(template=template_one, instructions="Do it")
    make_schedule(company=company, branch=branch_one, template=template_one, scheduled_time=time(9, 0))

    template_two = make_template(
        company=company, branch=branch_two,
        slug="daily-b", name="Daily B", assigned_user=owner,
    )
    make_template_version(template=template_two, instructions="Do it")
    make_schedule(company=company, branch=branch_two, template=template_two, scheduled_time=time(9, 0))

    instances = schedule_due_tasks(moment=timezone.make_aware(datetime(2026, 1, 5, 9, 30)))
    instance_one = next(instance for instance in instances if instance.branch_id == branch_one.id)
    instance_two = next(instance for instance in instances if instance.branch_id == branch_two.id)
    return owner, monitor, company, branch_one, branch_two, instance_one, instance_two


def test_review_queue_is_branch_scoped(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    _owner, monitor, company, branch_one, _branch_two, _instance_one, _instance_two = _task_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_job_role, make_branch_membership,
    )
    client = Client()
    client.force_login(monitor, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.get("/api/v1/reviews/queue")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert all(item["branch_id"] == str(branch_one.id) for item in response.json()["items"])


def test_review_policy_round_trip_and_decision_history(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company, _branch_one, _branch_two, instance, _instance_two = _task_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_job_role, make_branch_membership,
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    policy_response = client.patch(
        "/api/v1/reviews/policy",
        data={"employee_score_visibility": "detailed", "extra_evidence_required": True},
        content_type="application/json",
    )
    assert policy_response.status_code == 200
    assert policy_response.json()["extra_evidence_required"] is True

    decision_response = client.post(
        "/api/v1/reviews/decisions",
        data={"decision_type": "retry_same_task", "task_instance_id": str(instance.id), "reason": "recheck"},
        content_type="application/json",
    )
    assert decision_response.status_code == 201
    assert ReviewDecision.objects.count() == 1
    assert ReviewDecision.objects.first().generated_task_instance_id is not None


def test_review_dashboard_reports_company_trend(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    owner, _monitor, company, _branch_one, _branch_two, instance, _instance_two = _task_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_job_role, make_branch_membership,
    )
    instance.completed_at = timezone.now()
    instance.status = "completed"
    instance.save(update_fields=["completed_at", "status", "updated_at"])

    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.get("/api/v1/reviews/dashboard")
    assert response.status_code == 200
    assert response.json()["summary"]["completed_today"] >= 1


def test_monitor_cannot_decision_unassigned_branch(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    _owner, monitor, company, _branch_one, _branch_two, _instance_one, instance_two = _task_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_job_role, make_branch_membership,
    )
    client = Client()
    client.force_login(monitor, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.post(
        "/api/v1/reviews/decisions",
        data={"decision_type": "retry_same_task", "task_instance_id": str(instance_two.id), "reason": "unassigned branch"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert ReviewDecision.objects.count() == 0
