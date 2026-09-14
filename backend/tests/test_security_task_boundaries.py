"""Regression tests for user-level task boundaries and owner-only controls."""

from __future__ import annotations

from django.utils import timezone

from apps.evidence.models import TaskIssueReport
from apps.organizations.models import CompanyRole
from apps.tasks.models import TaskAssignmentMode, TaskInstance, TaskTemplateVersion, TaskTransferRequest


def _task_for(company, branch, assignee, make_template):
    template = make_template(
        company=company,
        branch=branch,
        assigned_user=assignee,
        assignment_mode=TaskAssignmentMode.NAMED_USER,
    )
    version = TaskTemplateVersion.objects.create(template=template, version_number=1, instructions="Complete safely.")
    return TaskInstance.objects.create(
        company=company,
        branch=branch,
        template=template,
        template_version=version,
        assigned_user=assignee,
        scheduled_for=timezone.now(),
        due_at=timezone.now(),
    )


def test_employee_cannot_access_a_colleagues_task_evidence_or_issues(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="boundary-owner")
    company = make_company(owner=owner, code="boundary-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee_a = make_user(login_id="boundary-a")
    employee_b = make_user(login_id="boundary-b")
    make_membership(user=employee_a, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=employee_b, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="boundary-branch")
    job_role = make_job_role(company=company, code="boundary-role")
    make_branch_membership(company=company, user=employee_a, branch=branch, job_role=job_role)
    make_branch_membership(company=company, user=employee_b, branch=branch, job_role=job_role)
    task = _task_for(company, branch, employee_b, make_template)
    issue = TaskIssueReport.objects.create(
        company=company,
        branch=branch,
        task_instance=task,
        submitted_by=employee_b,
        note="Blocked by a real issue.",
    )

    client = force_login_company(employee_a, company)
    assert client.get(f"/api/v1/evidence/tasks/{task.id}").status_code == 403
    assert client.post(
        "/api/v1/evidence/capture-sessions",
        data={"task_instance_id": str(task.id), "evidence_type": "note"},
        content_type="application/json",
    ).status_code == 403
    assert client.post(
        "/api/v1/evidence/issues",
        data={"task_instance_id": str(task.id), "note": "Not my task."},
        content_type="application/json",
    ).status_code == 403
    assert client.get(f"/api/v1/evidence/issues/{issue.id}/messages").status_code == 403
    assert client.post(
        f"/api/v1/evidence/issues/{issue.id}/messages",
        data={"task_instance_id": str(task.id), "message": "Not my discussion."},
        content_type="application/json",
    ).status_code == 403


def test_employee_cannot_decide_a_transfer_requested_to_them(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="transfer-owner")
    company = make_company(owner=owner, code="transfer-boundary-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee_a = make_user(login_id="transfer-a")
    employee_b = make_user(login_id="transfer-b")
    make_membership(user=employee_a, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=employee_b, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="transfer-boundary-branch")
    job_role = make_job_role(company=company, code="transfer-boundary-role")
    make_branch_membership(company=company, user=employee_a, branch=branch, job_role=job_role)
    make_branch_membership(company=company, user=employee_b, branch=branch, job_role=job_role)
    task = _task_for(company, branch, employee_a, make_template)
    transfer = TaskTransferRequest.objects.create(
        task_instance=task,
        requested_by=employee_a,
        requested_to=employee_b,
        reason="Need cover.",
    )

    client = force_login_company(employee_b, company)
    response = client.post(
        f"/api/v1/tasks/transfers/{transfer.id}/resolve",
        data={"approved": True},
        content_type="application/json",
    )
    assert response.status_code == 403


def test_monitor_cannot_read_owner_only_operational_controls(
    force_login_company,
    make_user,
    make_company,
    make_membership,
):
    owner = make_user(login_id="owner-controls")
    company = make_company(owner=owner, code="owner-controls-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="monitor-controls")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    client = force_login_company(monitor, company)

    for path in (
        "/api/v1/ai/provider",
        "/api/v1/ai/criteria",
        "/api/v1/ai/shadow",
        "/api/v1/connectors/enrollment",
        "/api/v1/connectors/health",
        "/api/v1/backups/policy",
        "/api/v1/backups/runs/list",
        "/api/v1/exports/policy",
        "/api/v1/exports/requests/list",
        "/api/v1/organizations/memberships",
        "/api/v1/agent/logs",
    ):
        assert client.get(path).status_code == 403, path


def test_monitor_can_create_a_version_only_for_a_template_in_their_branch(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="version-owner")
    company = make_company(owner=owner, code="version-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="version-monitor")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    employee = make_user(login_id="version-employee")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="version-branch")
    role = make_job_role(company=company, code="version-role")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role)
    template = make_template(company=company, branch=branch, assigned_user=employee)

    client = force_login_company(monitor, company)
    response = client.post(
        f"/api/v1/tasks/templates/{template.id}/versions",
        data={"instructions": "Close the store safely.", "checklist_definition": [{"label": "Lock door"}]},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["version_number"] == 1


def test_employee_task_request_is_scoped_and_a_monitor_can_resolve_it(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="request-owner")
    company = make_company(owner=owner, code="request-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="request-monitor")
    employee = make_user(login_id="request-employee")
    colleague = make_user(login_id="request-colleague")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=colleague, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="request-branch")
    role = make_job_role(company=company, code="request-role")
    for user in (monitor, employee, colleague):
        make_branch_membership(company=company, user=user, branch=branch, job_role=role)
    task = _task_for(company, branch, employee, make_template)
    colleague_task = _task_for(company, branch, colleague, make_template)

    employee_client = force_login_company(employee, company)
    denied = employee_client.post(
        "/api/v1/tasks/requests",
        data={
            "branch_id": str(branch.id),
            "task_instance_id": str(colleague_task.id),
            "kind": "cancellation",
            "reason": "Not my work.",
        },
        content_type="application/json",
    )
    assert denied.status_code == 403
    created = employee_client.post(
        "/api/v1/tasks/requests",
        data={
            "branch_id": str(branch.id),
            "task_instance_id": str(task.id),
            "kind": "cancellation",
            "reason": "Site is closed today.",
        },
        content_type="application/json",
    )
    assert created.status_code == 201

    monitor_client = force_login_company(monitor, company)
    resolved = monitor_client.post(
        f"/api/v1/tasks/requests/{created.json()['id']}/resolve",
        data={"approved": True, "decision_reason": "Confirmed by shift lead."},
        content_type="application/json",
    )
    assert resolved.status_code == 200
    task.refresh_from_db()
    assert task.status == "cancelled"
