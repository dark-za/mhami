from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO

from apps.tenancy.models import Company


pytestmark = pytest.mark.django_db


def test_seed_pilot_requires_password(monkeypatch):
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    # Ensure default env not prod; conftest sets it to config.settings.test,
    # so the guard should not trigger — we want the password guard.
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.test")
    with pytest.raises((CommandError, SystemExit)):
        call_command("seed_pilot", company="req-pass-co")
    assert not Company.objects.filter(code="req-pass-co").exists()


def test_seed_pilot_refuses_when_prod_settings(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    with pytest.raises(CommandError, match="non-production only|not allowed.*prod"):
        call_command("seed_pilot", company="prod-co", password="StrongPass123!Long")
    assert not Company.objects.filter(code="prod-co").exists()


def test_seed_pilot_refuses_prod_before_mutation_even_with_existing_company(monkeypatch):
    # Successful seed first, then attempt prod-seed with same code but --reset.
    # The prod guard must fire before any delete happens.
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.test")
    out = StringIO()
    call_command("seed_pilot", company="prod-guard-co", password="StrongPass123!Long", stdout=out)
    assert Company.objects.filter(code="prod-guard-co").exists()

    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    with pytest.raises(CommandError, match="non-production only|not allowed.*prod"):
        call_command("seed_pilot", company="prod-guard-co", password="StrongPass123!Long", reset=True)
    # Existing company must still exist — guard fired before mutation.
    assert Company.objects.filter(code="prod-guard-co").exists()


def test_seed_pilot_success_does_not_echo_password(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.test")
    password = "S3cure-Pilot-Pass-2026!"
    out = StringIO()
    call_command(
        "seed_pilot",
        company="ok-co",
        password=password,
        branches=1,
        employees_per_branch=1,
        stdout=out,
    )
    output = out.getvalue()
    assert password not in output
    assert "ok-co" in output
    assert Company.objects.filter(code="ok-co").exists()
    # Owner user should have been created with the provided password.
    from apps.identity.models import User

    owner = User.objects.get(login_id="ok-co-owner")
    assert owner.check_password(password)
