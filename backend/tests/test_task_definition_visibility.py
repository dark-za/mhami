"""Employee read-isolation tests for task templates and task schedules.

Confirms that an authenticated employee sees only their own assigned
work in GET /api/v1/tasks/templates and GET /api/v1/tasks/schedules.
Colleague rows, unassigned rows, and rows in other branches are excluded.
Owner and monitor full-branch visibility is preserved.
"""

from __future__ import annotations

from apps.organizations.models import CompanyRole


def test_employee_sees_only_own_templates_not_colleagues(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="vis-owner")
    company = make_company(owner=owner, code="vis-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee_a = make_user(login_id="vis-emp-a")
    employee_b = make_user(login_id="vis-emp-b")
    make_membership(user=employee_a, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=employee_b, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="vis-branch")
    role = make_job_role(company=company, code="vis-role")
    make_branch_membership(company=company, user=employee_a, branch=branch, job_role=role)
    make_branch_membership(company=company, user=employee_b, branch=branch, job_role=role)

    make_template(
        company=company, branch=branch,
        slug="tpl-a", name="Template A", assigned_user=employee_a,
    )
    make_template(
        company=company, branch=branch,
        slug="tpl-b", name="Template B", assigned_user=employee_b,
    )

    client = force_login_company(employee_a, company)
    response = client.get("/api/v1/tasks/templates")
    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()["templates"]}
    assert "tpl-a" in slugs
    assert "tpl-b" not in slugs


def test_employee_own_template_visible(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="vis2-owner")
    company = make_company(owner=owner, code="vis2-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="vis2-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="vis2-branch")
    role = make_job_role(company=company, code="vis2-role")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role)

    make_template(
        company=company, branch=branch,
        slug="my-tpl", name="My Template", assigned_user=employee,
    )

    client = force_login_company(employee, company)
    response = client.get("/api/v1/tasks/templates")
    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()["templates"]}
    assert "my-tpl" in slugs
    assert len(response.json()["templates"]) == 1


def test_employee_excluded_from_other_branch_templates(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="vis3-owner")
    company = make_company(owner=owner, code="vis3-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="vis3-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch_in = make_branch(company=company, code="vis3-in")
    branch_out = make_branch(company=company, code="vis3-out")
    role = make_job_role(company=company, code="vis3-role")
    make_branch_membership(company=company, user=employee, branch=branch_in, job_role=role)

    make_template(
        company=company, branch=branch_out,
        slug="other-branch-tpl", name="Other Branch", assigned_user=employee,
    )

    client = force_login_company(employee, company)
    response = client.get("/api/v1/tasks/templates")
    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()["templates"]}
    assert "other-branch-tpl" not in slugs


def test_owner_sees_all_branch_templates(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_template,
):
    owner = make_user(login_id="vis4-owner")
    company = make_company(owner=owner, code="vis4-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    branch = make_branch(company=company, code="vis4-branch")
    employee = make_user(login_id="vis4-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)

    make_template(
        company=company, branch=branch,
        slug="owner-sees-this", name="Other user template", assigned_user=employee,
    )
    make_template(
        company=company, branch=branch,
        slug="unassigned-tpl", name="Unassigned",
        assignment_mode="role_pool",
    )

    client = force_login_company(owner, company)
    response = client.get("/api/v1/tasks/templates")
    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()["templates"]}
    assert "owner-sees-this" in slugs
    assert "unassigned-tpl" in slugs


def test_monitor_sees_all_branch_templates(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="vis5-owner")
    company = make_company(owner=owner, code="vis5-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="vis5-mon")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    employee = make_user(login_id="vis5-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="vis5-branch")
    role = make_job_role(company=company, code="vis5-role")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)

    make_template(
        company=company, branch=branch,
        slug="mon-sees-this", name="Employee template", assigned_user=employee,
    )
    make_template(
        company=company, branch=branch,
        slug="unassigned-for-mon", name="Unassigned",
        assignment_mode="monitor_distributed",
    )

    client = force_login_company(monitor, company)
    response = client.get("/api/v1/tasks/templates")
    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()["templates"]}
    assert "mon-sees-this" in slugs
    assert "unassigned-for-mon" in slugs


def test_employee_unassigned_templates_excluded(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
):
    owner = make_user(login_id="vis6-owner")
    company = make_company(owner=owner, code="vis6-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="vis6-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="vis6-branch")
    role = make_job_role(company=company, code="vis6-role")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role)

    make_template(
        company=company, branch=branch,
        slug="assigned-to-me", name="Mine", assigned_user=employee,
    )
    make_template(
        company=company, branch=branch,
        slug="unassigned", name="Unassigned",
        assignment_mode="role_pool",
    )

    client = force_login_company(employee, company)
    response = client.get("/api/v1/tasks/templates")
    assert response.status_code == 200
    slugs = {t["slug"] for t in response.json()["templates"]}
    assert "assigned-to-me" in slugs
    assert "unassigned" not in slugs


def test_employee_sees_only_own_schedules_not_colleagues(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
    make_template_version,
    make_schedule,
):
    owner = make_user(login_id="sched-vis-owner")
    company = make_company(owner=owner, code="sched-vis-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee_a = make_user(login_id="sched-vis-a")
    employee_b = make_user(login_id="sched-vis-b")
    make_membership(user=employee_a, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=employee_b, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="sched-vis-branch")
    role = make_job_role(company=company, code="sched-vis-role")
    make_branch_membership(company=company, user=employee_a, branch=branch, job_role=role)
    make_branch_membership(company=company, user=employee_b, branch=branch, job_role=role)

    tpl_a = make_template(
        company=company, branch=branch,
        slug="sched-tpl-a", name="Schedule A", assigned_user=employee_a,
    )
    make_template_version(template=tpl_a)
    sched_a = make_schedule(company=company, branch=branch, template=tpl_a)

    tpl_b = make_template(
        company=company, branch=branch,
        slug="sched-tpl-b", name="Schedule B", assigned_user=employee_b,
    )
    make_template_version(template=tpl_b)
    sched_b = make_schedule(company=company, branch=branch, template=tpl_b)

    client = force_login_company(employee_a, company)
    response = client.get("/api/v1/tasks/schedules")
    assert response.status_code == 200
    schedule_ids = {s["id"] for s in response.json()["schedules"]}
    assert str(sched_a.id) in schedule_ids
    assert str(sched_b.id) not in schedule_ids


def test_employee_own_schedule_visible(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
    make_template_version,
    make_schedule,
):
    owner = make_user(login_id="sched-vis2-owner")
    company = make_company(owner=owner, code="sched-vis2-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="sched-vis2-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="sched-vis2-branch")
    role = make_job_role(company=company, code="sched-vis2-role")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role)

    tpl = make_template(
        company=company, branch=branch,
        slug="my-sched-tpl", name="My Schedule Template", assigned_user=employee,
    )
    make_template_version(template=tpl)
    sched = make_schedule(company=company, branch=branch, template=tpl)

    client = force_login_company(employee, company)
    response = client.get("/api/v1/tasks/schedules")
    assert response.status_code == 200
    schedule_ids = {s["id"] for s in response.json()["schedules"]}
    assert str(sched.id) in schedule_ids
    assert len(response.json()["schedules"]) == 1


def test_employee_excluded_from_other_branch_schedules(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
    make_template_version,
    make_schedule,
):
    owner = make_user(login_id="sched-vis3-owner")
    company = make_company(owner=owner, code="sched-vis3-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="sched-vis3-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch_in = make_branch(company=company, code="sched-vis3-in")
    branch_out = make_branch(company=company, code="sched-vis3-out")
    role = make_job_role(company=company, code="sched-vis3-role")
    make_branch_membership(company=company, user=employee, branch=branch_in, job_role=role)

    tpl = make_template(
        company=company, branch=branch_out,
        slug="out-branch-sched", name="Other Branch Schedule", assigned_user=employee,
    )
    make_template_version(template=tpl)
    sched = make_schedule(company=company, branch=branch_out, template=tpl)

    client = force_login_company(employee, company)
    response = client.get("/api/v1/tasks/schedules")
    assert response.status_code == 200
    schedule_ids = {s["id"] for s in response.json()["schedules"]}
    assert str(sched.id) not in schedule_ids


def test_owner_sees_all_branch_schedules(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_template,
    make_template_version,
    make_schedule,
):
    owner = make_user(login_id="sched-vis4-owner")
    company = make_company(owner=owner, code="sched-vis4-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    branch = make_branch(company=company, code="sched-vis4-branch")
    employee = make_user(login_id="sched-vis4-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)

    tpl_assigned = make_template(
        company=company, branch=branch,
        slug="owner-sched-assigned", name="Assigned to other", assigned_user=employee,
    )
    make_template_version(template=tpl_assigned)
    sched_assigned = make_schedule(company=company, branch=branch, template=tpl_assigned)

    tpl_unassigned = make_template(
        company=company, branch=branch,
        slug="owner-sched-unassigned", name="Unassigned schedule",
        assignment_mode="role_pool",
    )
    make_template_version(template=tpl_unassigned)
    sched_unassigned = make_schedule(company=company, branch=branch, template=tpl_unassigned)

    client = force_login_company(owner, company)
    response = client.get("/api/v1/tasks/schedules")
    assert response.status_code == 200
    schedule_ids = {s["id"] for s in response.json()["schedules"]}
    assert str(sched_assigned.id) in schedule_ids
    assert str(sched_unassigned.id) in schedule_ids


def test_employee_unassigned_schedules_excluded(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
    make_template_version,
    make_schedule,
):
    owner = make_user(login_id="sched-vis6-owner")
    company = make_company(owner=owner, code="sched-vis6-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    employee = make_user(login_id="sched-vis6-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="sched-vis6-branch")
    role = make_job_role(company=company, code="sched-vis6-role")
    make_branch_membership(company=company, user=employee, branch=branch, job_role=role)

    tpl_assigned = make_template(
        company=company, branch=branch,
        slug="sched-assigned-to-me", name="Mine", assigned_user=employee,
    )
    make_template_version(template=tpl_assigned)
    sched_assigned = make_schedule(company=company, branch=branch, template=tpl_assigned)

    tpl_unassigned = make_template(
        company=company, branch=branch,
        slug="sched-unassigned", name="Unassigned schedule",
        assignment_mode="role_pool",
    )
    make_template_version(template=tpl_unassigned)
    sched_unassigned = make_schedule(company=company, branch=branch, template=tpl_unassigned)

    client = force_login_company(employee, company)
    response = client.get("/api/v1/tasks/schedules")
    assert response.status_code == 200
    schedule_ids = {s["id"] for s in response.json()["schedules"]}
    assert str(sched_assigned.id) in schedule_ids
    assert str(sched_unassigned.id) not in schedule_ids


def test_monitor_sees_all_branch_schedules(
    force_login_company,
    make_user,
    make_company,
    make_branch,
    make_membership,
    make_job_role,
    make_branch_membership,
    make_template,
    make_template_version,
    make_schedule,
):
    owner = make_user(login_id="sched-vis5-owner")
    company = make_company(owner=owner, code="sched-vis5-co")
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    monitor = make_user(login_id="sched-vis5-mon")
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    employee = make_user(login_id="sched-vis5-emp")
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company, code="sched-vis5-branch")
    role = make_job_role(company=company, code="sched-vis5-role")
    make_branch_membership(company=company, user=monitor, branch=branch, job_role=role)

    tpl_assigned = make_template(
        company=company, branch=branch,
        slug="mon-sched-assigned", name="Assigned to other", assigned_user=employee,
    )
    make_template_version(template=tpl_assigned)
    sched_assigned = make_schedule(company=company, branch=branch, template=tpl_assigned)

    tpl_unassigned = make_template(
        company=company, branch=branch,
        slug="mon-sched-unassigned", name="Unassigned",
        assignment_mode="monitor_distributed",
    )
    make_template_version(template=tpl_unassigned)
    sched_unassigned = make_schedule(company=company, branch=branch, template=tpl_unassigned)

    client = force_login_company(monitor, company)
    response = client.get("/api/v1/tasks/schedules")
    assert response.status_code == 200
    schedule_ids = {s["id"] for s in response.json()["schedules"]}
    assert str(sched_assigned.id) in schedule_ids
    assert str(sched_unassigned.id) in schedule_ids
