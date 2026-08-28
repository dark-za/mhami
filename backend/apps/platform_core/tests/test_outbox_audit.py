from __future__ import annotations

import pytest

from apps.audit.services import record_audit_event
from apps.platform_core.services import record_outbox_event

pytestmark = pytest.mark.django_db


def test_outbox_event_is_created():
    event = record_outbox_event(
        event_name="core.health.changed",
        aggregate_type="system",
        aggregate_id="1",
        payload={"status": "ok"},
    )
    assert event.event_name == "core.health.changed"


def test_audit_event_is_append_only():
    event = record_audit_event(
        event_type="SYSTEM_BOOTSTRAP",
        target_type="system",
        target_id="1",
    )
    with pytest.raises(Exception):
        event.delete()
