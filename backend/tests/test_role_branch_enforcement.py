from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.test import Client
from django.utils import timezone

from apps.organizations.models import CompanyRole, UserBranchMembership

pytestmark = pytest.mark.django_db


def _login(client: Client, user, company):
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    return client


# ---------------------------------------------------------------------------
# 1. Multi-branch assignments
# ---------------------------------------------------------------------------

def test_monitor_can_have_multiple_branch_assignments(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership):
    owner = make_user(login_id="owner-multi")
    company = make_company(owner=owner, code="multi-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="monitor-multi")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch_a = make_branch(company=company, code="branch-a", name="A")
    branch_b = make_branch(company=company, code="branch-b", name="B")
    role = make_job_role(company=company, name="Staff", code="staff-multi")
    make_branch_membership(company=company, user=monitor, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=monitor, branch=branch_b, job_role=role)
    assert UserBranchMembership.objects.filter(user=monitor, active=True).count() == 2
    # duplicate assignment to same branch must be prevented
    with pytest.raises(IntegrityError):
        make_branch_membership(company=company, user=monitor, branch=branch_a, job_role=role)


def test_monitor_cross_branch_assignment_rejected(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership):
    owner = make_user(login_id="owner-cross")
    company = make_company(owner=owner, code="cross-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="monitor-cross")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch_a = make_branch(company=company, code="ba", name="Branch A")
    branch_b = make_branch(company=company, code="bb", name="Branch B")
    role = make_job_role(company=company, name="Staff", code="staff-cross")
    make_branch_membership(company=company, user=monitor, branch=branch_a, job_role=role)
    employee = make_user(login_id="employee-cross")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)

    client = Client()
    _login(client, monitor, company)
    response = client.post(
        "/api/v1/auth/company/branch-memberships",
        data={"user_id": str(employee.id), "branch_id": str(branch_b.id), "job_role_id": str(role.id)},
        content_type="application/json",
    )
    assert response.status_code == 403


def test_monitor_cannot_create_owner_or_monitor_users(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership):
    owner = make_user(login_id="owner-create")
    company = make_company(owner=owner, code="create-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="monitor-create")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, code="main-create", name="Main")
    role = make_job_role(company=company, name="Staff", code="staff-create")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)

    client = Client()
    _login(client, monitor, company)

    for forbidden_role in [CompanyRole.OWNER, CompanyRole.MONITOR]:
        resp = client.post(
            "/api/v1/auth/company/users",
            data={"login_id": f"new-{forbidden_role}", "password": "Mha!mi-Test-2026#", "display_name": "New", "role": forbidden_role},
            content_type="application/json",
        )
        assert resp.status_code == 403, resp.content.decode()

    # A monitor can create an employee only inside an assigned branch and
    # with an explicit descriptive job role.
    ok = client.post(
        "/api/v1/auth/company/users",
        data={
            "login_id": "new-employee-ok",
            "password": "Mha!mi-Test-2026#",
            "display_name": "New Emp",
            "role": CompanyRole.EMPLOYEE,
            "branch_id": str(branch.id),
            "job_role_id": str(role.id),
        },
        content_type="application/json",
    )
    assert ok.status_code == 201


def test_owner_can_create_all_roles(make_user, make_company, make_membership):
    owner = make_user(login_id="owner-all-roles")
    company = make_company(owner=owner, code="all-roles-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    client = Client()
    _login(client, owner, company)
    for role in [CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE]:
        resp = client.post(
            "/api/v1/auth/company/users",
            data={"login_id": f"owner-new-{role}", "password": "Mha!mi-Test-2026#", "role": role},
            content_type="application/json",
        )
        assert resp.status_code == 201, resp.content.decode()


# ---------------------------------------------------------------------------
# 2. Employee task privacy
# ---------------------------------------------------------------------------

def _setup_task_env(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule):
    owner = make_user(login_id="task-owner-priv")
    company = make_company(owner=owner, code="task-priv-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    branch = make_branch(company=company, code="priv-branch", name="Priv Branch")
    role = make_job_role(company=company, name="Staff", code="staff-priv")
    emp_a = make_user(login_id="emp-a")
    emp_b = make_user(login_id="emp-b")
    make_membership(user=emp_a, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=emp_b, company=company, role=CompanyRole.EMPLOYEE)
    make_branch_membership(company=company, user=emp_a, branch=branch, job_role=role)
    make_branch_membership(company=company, user=emp_b, branch=branch, job_role=role)
    # also give owner branch? owner has implicit all branches
    template_a = make_template(company=company, branch=branch, slug="tpl-a", name="Tpl A", assigned_user=emp_a)
    make_template_version(template=template_a)
    template_b = make_template(company=company, branch=branch, slug="tpl-b", name="Tpl B", assigned_user=emp_b)
    make_template_version(template=template_b)
    # create instances directly via model
    from apps.tasks.models import TaskInstance
    from django.utils import timezone
    # ensure instance creation
    inst_a = TaskInstance.objects.create(
        company=company, branch=branch, template=template_a, template_version=template_a.versions.first(),
        scheduled_for=timezone.now(), due_at=timezone.now(),
        assigned_user=emp_a, status="pending",
    )
    inst_b = TaskInstance.objects.create(
        company=company, branch=branch, template=template_b, template_version=template_b.versions.first(),
        scheduled_for=timezone.now(), due_at=timezone.now(),
        assigned_user=emp_b, status="pending",
    )
    return owner, company, branch, role, emp_a, emp_b, inst_a, inst_b


def test_employee_task_list_isolation(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule):
    owner, company, branch, role, emp_a, emp_b, inst_a, inst_b = _setup_task_env(
        make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule
    )
    client = Client()
    _login(client, emp_a, company)
    resp = client.get("/api/v1/tasks/instances")
    assert resp.status_code == 200
    ids = {i["id"] for i in resp.json()["instances"]}
    assert str(inst_a.id) in ids
    assert str(inst_b.id) not in ids


def test_employee_cannot_start_or_complete_another_users_task(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule):
    owner, company, branch, role, emp_a, emp_b, inst_a, inst_b = _setup_task_env(
        make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule
    )
    client = Client()
    _login(client, emp_a, company)
    start = client.post(f"/api/v1/tasks/instances/{inst_b.id}/start", data={}, content_type="application/json")
    assert start.status_code == 403
    complete = client.post(f"/api/v1/tasks/instances/{inst_b.id}/complete", data={}, content_type="application/json")
    assert complete.status_code == 403
    # transfer for another user's task also rejected
    transfer = client.post(
        f"/api/v1/tasks/instances/{inst_b.id}/transfers",
        data={"requested_to_id": str(emp_b.id)},
        content_type="application/json",
    )
    assert transfer.status_code == 403


def test_employee_transfer_requires_own_task_and_target_branch_assignment(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule):
    owner = make_user(login_id="owner-transfer-emp")
    company = make_company(owner=owner, code="transfer-emp-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    branch_a = make_branch(company=company, code="br-a", name="Branch A")
    branch_b = make_branch(company=company, code="br-b", name="Branch B")
    role = make_job_role(company=company, name="Staff", code="staff-t")
    emp_a = make_user(login_id="emp-transfer-a")
    emp_b = make_user(login_id="emp-transfer-b")
    emp_c = make_user(login_id="emp-transfer-c")
    make_membership(user=emp_a, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=emp_b, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=emp_c, company=company, role=CompanyRole.EMPLOYEE)
    make_branch_membership(company=company, user=emp_a, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=emp_b, branch=branch_a, job_role=role)
    make_branch_membership(company=company, user=emp_c, branch=branch_b, job_role=role)
    template = make_template(company=company, branch=branch_a, slug="tpl-t", name="Tpl T", assigned_user=emp_a)
    make_template_version(template=template)
    from apps.tasks.models import TaskInstance
    inst = TaskInstance.objects.create(
        company=company, branch=branch_a, template=template, template_version=template.versions.first(),
        scheduled_for=timezone.now(), due_at=timezone.now(),
        assigned_user=emp_a, status="pending",
    )
    client = Client()
    _login(client, emp_a, company)
    # valid target in same branch should succeed (emp_b)
    ok = client.post(
        f"/api/v1/tasks/instances/{inst.id}/transfers",
        data={"requested_to_id": str(emp_b.id)},
        content_type="application/json",
    )
    assert ok.status_code == 201
    # target in different branch should be rejected (emp_c)
    bad = client.post(
        f"/api/v1/tasks/instances/{inst.id}/transfers",
        data={"requested_to_id": str(emp_c.id)},
        content_type="application/json",
    )
    assert bad.status_code == 403


def test_employees_cannot_claim_arbitrary_tasks(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule):
    owner, company, branch, role, emp_a, emp_b, inst_a, inst_b = _setup_task_env(
        make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule
    )
    client = Client()
    _login(client, emp_a, company)
    claim = client.post(f"/api/v1/tasks/instances/{inst_a.id}/claim", data={}, content_type="application/json")
    assert claim.status_code == 403
    # also cannot claim other's task
    claim_other = client.post(f"/api/v1/tasks/instances/{inst_b.id}/claim", data={}, content_type="application/json")
    assert claim_other.status_code == 403


def test_owner_and_monitor_can_claim_branch_scoped(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule):
    owner = make_user(login_id="owner-claim")
    company = make_company(owner=owner, code="claim-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="monitor-claim")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, code="claim-branch", name="Claim Branch")
    role = make_job_role(company=company, name="Staff", code="staff-claim")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)
    template = make_template(company=company, branch=branch, slug="tpl-claim", name="Tpl Claim")
    make_template_version(template=template)
    from apps.tasks.models import TaskInstance
    inst = TaskInstance.objects.create(
        company=company, branch=branch, template=template, template_version=template.versions.first(),
        scheduled_for=timezone.now(), due_at=timezone.now(),
        status="pending",
    )
    client = Client()
    _login(client, owner, company)
    resp = client.post(f"/api/v1/tasks/instances/{inst.id}/claim", data={}, content_type="application/json")
    assert resp.status_code == 200

    # monitor also allowed
    inst2 = TaskInstance.objects.create(
        company=company, branch=branch, template=template, template_version=template.versions.first(),
        scheduled_for=timezone.now(), due_at=timezone.now(),
        status="pending",
    )
    client2 = Client()
    _login(client2, monitor, company)
    resp2 = client2.post(f"/api/v1/tasks/instances/{inst2.id}/claim", data={}, content_type="application/json")
    assert resp2.status_code == 200


def test_transfer_list_for_employee_isolated(make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule):
    owner, company, branch, role, emp_a, emp_b, inst_a, inst_b = _setup_task_env(
        make_user, make_company, make_membership, make_branch, make_job_role, make_branch_membership, make_template, make_template_version, make_schedule
    )
    from apps.tasks.models import TaskTransferRequest
    # create transfers linked to both instances
    t1 = TaskTransferRequest.objects.create(task_instance=inst_a, requested_by=emp_a, requested_to=emp_b)
    t2 = TaskTransferRequest.objects.create(task_instance=inst_b, requested_by=emp_b, requested_to=emp_a)
    client = Client()
    _login(client, emp_a, company)
    resp = client.get("/api/v1/tasks/transfers")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()["transfers"]}
    # emp_a should see t1 (assigned to them) and t2? t2 is requested_to emp_a but task not assigned to them; but they initiated? Actually t1 requested_by emp_a, t2 requested_to emp_a.
    # t1: task assigned to emp_a -> included, t2: task assigned to emp_b but requested_to is emp_a -> but spec says initiated OR assigned. t1 matches both, t2 matches requested_to == not requested_by but task not assigned. However our filter is Q(assigned_user=user) | Q(requested_by=user). So t1 yes, t2 no (requested_by is emp_b). But t2 requested_to is emp_a – should not be included per spec? Spec says "only transfers related to tasks assigned to them or transfers they initiated" – so t2 would not be included unless emp_a initiated. That's correct to be excluded.
    assert str(t1.id) in ids
    assert str(t2.id) not in ids

    # owner sees both via branch scoped
    client_owner = Client()
    _login(client_owner, owner, company)
    resp_owner = client_owner.get("/api/v1/tasks/transfers")
    assert resp_owner.status_code == 200
    owner_ids = {t["id"] for t in resp_owner.json()["transfers"]}
    assert str(t1.id) in owner_ids
    assert str(t2.id) in owner_ids
