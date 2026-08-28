from __future__ import annotations

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.organizations.models import CompanyRole
from apps.tasks.models import TaskAssignmentMode
from apps.tasks.services import request_transfer, schedule_due_tasks


pytestmark = pytest.mark.django_db


def _setup_company(
    make_user,
    make_company,
    make_membership,
    make_branch,
    make_template,
    make_template_version,
    make_schedule,
    *,
    owner_login: str = "task-owner",
    employee_login: str | None = None,
    code: str = "task-co",
    name: str = "Task Co",
    template_slug: str = "daily-clean",
    template_name: str = "Daily clean",
):
    """Build owner+optional employee, company, branch, and scheduled template."""
    owner = make_user(login_id=owner_login, display_name="Owner")
    company = make_company(name=name, code=code, owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = None
    if employee_login:
        employee = make_user(login_id=employee_login, display_name="Employee")
        make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="main", name="Main")
    template = make_template(
        company=company, branch=branch,
        slug=template_slug, name=template_name, assigned_user=owner,
    )
    make_template_version(template=template)
    make_schedule(company=company, branch=branch, template=template, scheduled_time=timezone.now().time())
    return owner, employee, company, branch, template


def test_task_template_api_and_scheduler_trigger(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    _owner, _employee, company, _branch, _template = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        template_slug="seed-template", template_name="Seed template",
    )
    # no force_login_company; this test exercises the API with manual session
    from django.test import Client
    from apps.identity.models import User  # noqa: F401
    owner = User.objects.get(login_id="task-owner")
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    create_response = client.post(
        "/api/v1/tasks/templates",
        data={
            "company_id": str(company.id),
            "branch_id": str(_branch.id),
            "slug": "daily-clean",
            "name": "Daily clean",
            "assignment_mode": TaskAssignmentMode.NAMED_USER,
        },
        content_type="application/json",
    )
    assert create_response.status_code == 201

    list_response = client.get("/api/v1/tasks/templates")
    assert list_response.status_code == 200
    slugs = {t["slug"] for t in list_response.json()["templates"]}
    assert "daily-clean" in slugs


@freeze_time("2026-01-05 09:30:00+00:00")
def test_task_instances_are_limited_to_the_active_branch(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    owner, employee, company, branch_one, _ = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        owner_login="branch-owner", employee_login="branch-employee",
        code="branch-co", name="Branch Co",
        template_slug="clean-a", template_name="clean-a",
    )
    branch_two = make_branch(company=company, code="b", name="B")
    role = make_job_role(company=company, name="Staff", code="staff")
    make_branch_membership(company=company, user=employee, branch=branch_one, job_role=role)

    # Second scheduled template on branch_two for the same employee
    template_two = make_template(
        company=company, branch=branch_two,
        slug="clean-b", name="clean-b", assigned_user=employee,
    )
    make_template_version(template=template_two)
    make_schedule(company=company, branch=branch_two, template=template_two, scheduled_time=timezone.now().time())

    schedule_due_tasks()

    from django.test import Client
    client = Client()
    client.force_login(employee, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.get("/api/v1/tasks/instances")
    assert response.status_code == 200
    instances = response.json()["instances"]
    assert len(instances) == 1
    assert instances[0]["branch"] == str(branch_one.id)


def test_transfer_listing_and_completion_endpoint(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner, _employee, company, _branch, _template = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        owner_login="task-owner-2", code="task-co-2", name="Task Co 2",
        template_slug="daily-clean-2", template_name="Daily clean 2",
    )
    instance = schedule_due_tasks()[0]

    from django.test import Client
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    start_response = client.post(f"/api/v1/tasks/instances/{instance.id}/start", data={}, content_type="application/json")
    assert start_response.status_code == 200

    complete_response = client.post(f"/api/v1/tasks/instances/{instance.id}/complete", data={}, content_type="application/json")
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"

    transfers_response = client.get("/api/v1/tasks/transfers")
    assert transfers_response.status_code == 200
    assert transfers_response.json()["transfers"] == []


def test_employee_cannot_create_task_templates_or_run_scheduler(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    owner, employee, company, branch, _ = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        owner_login="permissions-owner", employee_login="permissions-employee",
        code="permissions-co", name="Permissions Co",
    )
    role = make_job_role(company=company, name="Staff", code="staff")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role)

    from django.test import Client
    from apps.tasks.models import TaskTemplate
    client = Client()
    client.force_login(employee, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    create_response = client.post(
        "/api/v1/tasks/templates",
        data={
            "company_id": str(company.id),
            "branch_id": str(branch.id),
            "slug": "forbidden-template",
            "name": "Forbidden template",
            "assignment_mode": TaskAssignmentMode.NAMED_USER,
        },
        content_type="application/json",
    )
    scheduler_response = client.post(
        "/api/v1/tasks/scheduler/run",
        data={},
        content_type="application/json",
    )

    assert create_response.status_code == 403
    assert scheduler_response.status_code == 403
    assert not TaskTemplate.objects.filter(slug="forbidden-template").exists()


def test_owner_cannot_create_task_objects_with_another_company_scope(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner_a, _, company_a, _, _ = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        owner_login="scope-owner-a", code="scope-a", name="Scope A",
        template_slug="scope-a-tpl", template_name="Scope A template",
    )
    owner_b, _, company_b, branch_b, _ = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        owner_login="scope-owner-b", code="scope-b", name="Scope B",
        template_slug="scope-b-tpl", template_name="Scope B template",
    )
    from django.test import Client
    from apps.tasks.models import TaskTemplate
    client = Client()
    client.force_login(owner_a, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company_a.id)
    session.save()

    response = client.post(
        "/api/v1/tasks/templates",
        data={
            "company_id": str(company_b.id),
            "branch_id": str(branch_b.id),
            "slug": "cross-tenant",
            "name": "Cross tenant",
            "assignment_mode": TaskAssignmentMode.NAMED_USER,
        },
        content_type="application/json",
    )

    assert response.status_code == 403
    assert not TaskTemplate.objects.filter(slug="cross-tenant").exists()


@freeze_time("2026-01-05 09:30:00+00:00")
def test_user_cannot_resolve_another_company_transfer(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner_a, _, company_a, _, _ = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        owner_login="transfer-owner-a", code="transfer-a", name="Transfer A",
        template_slug="transfer-a-tpl", template_name="Transfer A template",
    )
    owner_b, _, company_b, branch_b, _ = _setup_company(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        owner_login="transfer-owner-b", code="transfer-b", name="Transfer B",
        template_slug="transfer-b-tpl", template_name="Transfer B template",
    )
    target_b = make_user(login_id="transfer-target-b", display_name="Target B")
    make_membership(user=target_b, company=company_b, role=CompanyRole.EMPLOYEE)

    instance = next(
        instance
        for instance in schedule_due_tasks()
        if instance.company_id == company_b.id and instance.branch_id == branch_b.id
    )
    transfer = request_transfer(str(instance.id), owner_b, target_b, "Shift handoff")
    from django.test import Client
    client = Client()
    client.force_login(owner_a, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company_a.id)
    session.save()

    response = client.post(
        f"/api/v1/tasks/transfers/{transfer.id}/resolve",
        data={"approved": True},
        content_type="application/json",
    )

    transfer.refresh_from_db()
    assert response.status_code == 403
    assert transfer.status == "pending"
