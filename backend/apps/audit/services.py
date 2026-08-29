from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from django.apps import apps
from django.db import transaction

from .models import AuditEvent
from apps.platform_core.request_id import get_request_id


@dataclass(frozen=True, slots=True)
class AuditTrailEntry:
    id: UUID
    event_type: str
    actor_id: str
    target_type: str
    target_id: str
    branch_id: str
    request_id: UUID
    executed_via: str
    agent_tool_name: str | None
    agent_grant_id: str | None
    metadata: Mapping[str, object]


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


def get_audit_trail(*, request_id: UUID | None = None) -> list[AuditTrailEntry]:
    """Return audit rows annotated with agent execution metadata.

    MCP agent attribution lives in ``agent_access.AgentActionLog`` and is
    correlated through the existing ``AuditEvent.request_id`` field so the
    hash-protected audit model does not need a schema change.
    """
    events = AuditEvent.objects.order_by("timestamp", "id")
    if request_id is not None:
        events = events.filter(request_id=request_id)

    AgentActionLog = apps.get_model("agent_access", "AgentActionLog")
    action_logs = AgentActionLog.objects.filter(
        request_id__in=events.values_list("request_id", flat=True)
    ).select_related("grant")
    agent_by_request_id = {log.request_id: log for log in action_logs}

    entries: list[AuditTrailEntry] = []
    for event in events:
        agent_log = agent_by_request_id.get(event.request_id)
        entries.append(
            AuditTrailEntry(
                id=event.id,
                event_type=event.event_type,
                actor_id=event.actor_id,
                target_type=event.target_type,
                target_id=event.target_id,
                branch_id=event.branch_id,
                request_id=event.request_id,
                executed_via="agent" if agent_log else "human",
                agent_tool_name=agent_log.tool_name if agent_log else None,
                agent_grant_id=str(agent_log.grant_id) if agent_log else None,
                metadata=event.metadata,
            )
        )
    return entries


def verify_audit_chain() -> bool:
    previous_hash = ""
    for event in AuditEvent.objects.order_by("timestamp", "id").iterator():
        if not event.verify_integrity(previous_hash):
            return False
        previous_hash = event.event_hash
    return True
