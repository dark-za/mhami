from __future__ import annotations

import io
import pytest
from django.core.management import call_command

from apps.organizations.models import Branch, JobRole
from apps.tasks.models import TaskTemplate, TaskSchedule
from apps.ai_gateway.models import AIAnalysisCriterion


@pytest.mark.django_db
def test_seed_company_defaults(make_user, make_company):
    owner = make_user(login_id="defaults-owner", display_name="Defaults Owner")
    company = make_company(name="Test Defaults Corp", code="test-defaults", owner=owner)

    out = io.StringIO()
    call_command("seed_company_defaults", "--company-code", company.code, stdout=out)

    output = out.getvalue()
    assert "Successfully seeded company defaults" in output

    # Check branches
    branches = Branch.objects.filter(company=company)
    assert branches.count() == 2
    assert set(branches.values_list("code", flat=True)) == {"main-ruh", "branch-jed"}

    # Check job roles
    roles = JobRole.objects.filter(company=company)
    assert roles.count() == 3
    assert "ops-supervisor" in roles.values_list("code", flat=True)

    # Check task templates
    templates = TaskTemplate.objects.filter(company=company)
    assert templates.count() == 2
    assert TaskSchedule.objects.filter(company=company).count() == 2

    # Check AI criteria
    assert AIAnalysisCriterion.objects.filter(company=company).count() == 1

    # Running a second time is idempotent
    call_command("seed_company_defaults", "--company-code", company.code, stdout=out)
    assert Branch.objects.filter(company=company).count() == 2
