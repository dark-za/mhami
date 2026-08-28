"""Unified outbox event writer.

The platform's modules publish domain events to consumers (notifications,
exports, audit aggregators) by writing :class:`OutboxEvent` rows inside the
same transaction as the business change. A relay then publishes the events
to the broker. This module provides:

- :class:`OutboxEventBuilder` — a small dataclass that captures the event
  fields without forcing callers to know about the database model.
- :func:`emit` — atomic write that respects the active transaction.
- :func:`emit_audit_and_outbox` — combined helper for the common case of
  writing both an audit row and a correlated outbox event.

Why not just call :func:`apps.platform_core.services.record_outbox_event`?
The legacy helper was verbose and never adopted outside ``platform_core``
itself. ``emit`` is the new, single entry point.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditEvent

from .models import OutboxEvent
from .request_id import get_request_id


@dataclass(frozen=True, slots=True)
class OutboxEventBuilder:
    """Lightweight value object describing an outbox event.

    Use :func:`emit` to persist it inside the active transaction. The
    ``headers`` slot is reserved for trace propagation and consumer
    routing keys.
    """

    event_name: str
    aggregate_type: str
    aggregate_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    request_id: UUID | None = None

    def with_request_id(self, request_id: UUID) -> "OutboxEventBuilder":
        return OutboxEventBuilder(
            event_name=self.event_name,
            aggregate_type=self.aggregate_type,
            aggregate_id=self.aggregate_id,
            payload=self.payload,
            headers=self.headers,
            request_id=request_id,
        )


@transaction.atomic
def emit(event: OutboxEventBuilder) -> OutboxEvent:
    """Persist an :class:`OutboxEvent` row inside the active transaction.

    Returns the saved model so callers can chain follow-up actions
    (e.g. dispatching to a notification handler). The row is committed
    when the surrounding ``transaction.atomic`` block exits successfully.
    """
    return OutboxEvent.objects.create(
        event_name=event.event_name,
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        payload=dict(event.payload),
        request_id=event.request_id or UUID(get_request_id()),
    )


@transaction.atomic
def emit_audit_and_outbox(
    *,
    audit_event_type: str,
    audit_target_type: str,
    audit_target_id: str,
    actor_id: str | None = None,
    branch_id: str | None = None,
    audit_metadata: Mapping[str, Any] | None = None,
    audit_before: Mapping[str, Any] | None = None,
    audit_after: Mapping[str, Any] | None = None,
    outbox: OutboxEventBuilder,
) -> tuple[AuditEvent, OutboxEvent]:
    """Write a correlated audit row and outbox event atomically.

    The audit row's ``request_id`` is forwarded into the outbox event so
    consumers can trace the originating HTTP request end-to-end. This is
    the canonical entry point for service-layer mutations that publish a
    domain event.
    """
    audit = AuditEvent.objects.create(
        event_type=audit_event_type,
        actor_id=actor_id or "",
        target_type=audit_target_type,
        target_id=audit_target_id,
        branch_id=branch_id or "",
        before=dict(audit_before or {}),
        after=dict(audit_after or {}),
        metadata=dict(audit_metadata or {}),
    )
    outbox_event = emit(outbox.with_request_id(audit.request_id))
    return audit, outbox_event


def quick_event(
    *,
    event_name: str,
    aggregate_type: str,
    aggregate_id: str,
    **payload: Any,
) -> OutboxEventBuilder:
    """Shorthand for one-line event construction.

    Example::

        emit(quick_event(event_name="exports.completed",
                         aggregate_type="export_request",
                         aggregate_id=str(req.id),
                         file_name=req.file_name,
                         request_id=str(req.id)))
    """
    return OutboxEventBuilder(
        event_name=event_name,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
    )


__all__ = [
    "OutboxEventBuilder",
    "emit",
    "emit_audit_and_outbox",
    "quick_event",
]


# Helper kept for backward compatibility with the audit service that
# previously read the current request ID synchronously.
_now = staticmethod(lambda: timezone.now())  # pragma: no cover
_uuid4 = staticmethod(uuid4)  # pragma: no cover
