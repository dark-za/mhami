from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.audit.models import AuditEvent
from apps.audit.services import record_audit_event, verify_audit_chain

pytestmark = pytest.mark.django_db


def test_record_audit_event_persists_context():
    event = record_audit_event(
        event_type="TEST_EVENT",
        target_type="company",
        target_id="company-1",
        actor_id="user-1",
        branch_id="branch-1",
        before={"status": "trial"},
        after={"status": "active"},
        metadata={"source": "unit-test"},
    )
    saved = AuditEvent.objects.get(id=event.id)
    assert saved.event_type == "TEST_EVENT"
    assert saved.target_id == "company-1"
    assert saved.after["status"] == "active"
    assert saved.metadata["source"] == "unit-test"


def test_audit_event_delete_is_forbidden():
    event = record_audit_event(
        event_type="APPEND_ONLY",
        target_type="system",
        target_id="1",
    )
    with pytest.raises(ValidationError):
        event.delete()


def test_audit_event_update_is_rejected():
    event = record_audit_event(
        event_type="IMMUTABLE",
        target_type="system",
        target_id="1",
    )
    event.event_type = "CHANGED"
    with pytest.raises(ValidationError):
        event.save()


def test_audit_events_form_a_tamper_evident_chain():
    first = record_audit_event(event_type="CHAIN_FIRST", target_type="system", target_id="1")
    second = record_audit_event(event_type="CHAIN_SECOND", target_type="system", target_id="2")

    assert first.previous_hash == ""
    assert second.previous_hash == first.event_hash
    assert len(first.event_hash) == 64
    assert len(first.integrity_hmac) == 64
    assert verify_audit_chain() is True

    AuditEvent.objects.filter(pk=first.pk).update(metadata={"tampered": True})
    assert verify_audit_chain() is False