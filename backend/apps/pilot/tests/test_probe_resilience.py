from __future__ import annotations

import inspect

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

pytestmark = pytest.mark.django_db


def test_probe_resilience_rejects_prod_before_any_mutation(monkeypatch):
    """Prod guard must fire before _create_probe or any DB write."""
    from apps.pilot.management.commands import probe_resilience

    def _unexpected_probe(*args, **kwargs):
        raise AssertionError("Production guard must run before probe creation")

    monkeypatch.setattr(probe_resilience.Command, "_create_probe", _unexpected_probe)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    with pytest.raises(CommandError, match="non-production only"):
        call_command("probe_resilience")


def test_no_static_pilot_pass_credential():
    source = inspect.getsource(
        __import__(
            "apps.pilot.management.commands.probe_resilience",
            fromlist=["probe_resilience"],
        )
    )
    assert "PilotPass" not in source, "Static PilotPass credential must not appear in command source"
