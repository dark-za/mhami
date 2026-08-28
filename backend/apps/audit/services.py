from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from django.db import transaction

from .models import AuditEvent
from apps.platform_core.request_id import get_request_id


@transaction.atomic
def record_audit_event(
    *,
    event_type: str,
    target_type: str,
    target_id: str,
    actor_id: str | None = None,
    branch_id: str | None = None,
    request_id: UUID | None = None,
    before: Mapping[str, object] | None = None,
    after: Mapping[str, object] | None = None,
    metadata: Mapping[str, object] | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        event_type=event_type,
        actor_id=actor_id or "",
        target_type=target_type,
        target_id=target_id,
        branch_id=branch_id or "",
        request_id=request_id or UUID(get_request_id()),
        before=dict(before or {}),
        after=dict(after or {}),
        metadata=dict(metadata or {}),
    )


def verify_audit_chain() -> bool:
    previous_hash = ""
    for event in AuditEvent.objects.order_by("timestamp", "id").iterator():
        if not event.verify_integrity(previous_hash):
            return False
        previous_hash = event.event_hash
    return True
