from __future__ import annotations

from collections.abc import Callable, Mapping
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.identity.models import User
from apps.platform_core.models import OutboxEvent
from apps.tenancy.models import Company

from .models import Notification, NotificationSeverity

SUBSCRIBED_EVENT_NAMES = ("backup.completed", "backup.restore.completed", "exports.completed")


def _find_company_owner(company_id: str) -> tuple[Company, User] | None:
    try:
        company = Company.objects.filter(id=UUID(company_id)).select_related("owner").first()
    except ValueError:
        return None
    if company is None or company.owner_id is None:
        return None
    return company, company.owner


@transaction.atomic
def create_notification(
    *,
    company: Company,
    user: User,
    notification_type: str,
    title: str,
    body: str = "",
    severity: str = "info",
    metadata: Mapping[str, object] | None = None,
    outbox_event: OutboxEvent | None = None,
) -> Notification | None:
    if outbox_event is not None and Notification.objects.filter(outbox_event_id=outbox_event.id).exists():
        return None
    notification = Notification.objects.create(
        company=company,
        user=user,
        type=notification_type,
        title=title,
        body=body,
        severity=severity,
        metadata=dict(metadata or {}),
        outbox_event=outbox_event,
    )
    record_audit_event(
        event_type="NOTIFICATION_CREATED",
        target_type="notification",
        target_id=str(notification.id),
        actor_id=str(user.id),
        branch_id="",
        metadata={"type": notification_type, "severity": severity},
    )
    return notification


def mark_notification_read(notification: Notification, *, actor: User) -> Notification:
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at", "updated_at"])
        record_audit_event(
            event_type="NOTIFICATION_READ",
            target_type="notification",
            target_id=str(notification.id),
            actor_id=str(actor.id),
            branch_id="",
            metadata={"batch": False},
        )
    return notification


def mark_notifications_read(notification_ids: list[str], *, company: Company, user: User) -> int:
    unread = Notification.objects.filter(company=company, user=user, id__in=notification_ids, read_at__isnull=True)
    ids = list(unread.values_list("id", flat=True))
    count = unread.update(read_at=timezone.now())
    for notification_id in ids:
        record_audit_event(
            event_type="NOTIFICATION_READ",
            target_type="notification",
            target_id=str(notification_id),
            actor_id=str(user.id),
            branch_id="",
            metadata={"batch": True},
        )
    return count


def _handle_backup_completed(event: OutboxEvent) -> None:
    payload = event.payload
    owner = _find_company_owner(str(payload.get("company_id", "")))
    if owner is None:
        return
    company, user = owner
    artifact_name = str(payload.get("artifact_name", ""))
    create_notification(
        company=company,
        user=user,
        notification_type="backup.completed",
        title="Backup completed",
        body=f"Backup artifact {artifact_name} is ready." if artifact_name else "A backup artifact is ready.",
        severity=NotificationSeverity.SUCCESS,
        metadata={"artifact_name": artifact_name},
        outbox_event=event,
    )


def _handle_backup_restore_completed(event: OutboxEvent) -> None:
    payload = event.payload
    owner = _find_company_owner(str(payload.get("company_id", "")))
    if owner is None:
        return
    company, user = owner
    create_notification(
        company=company,
        user=user,
        notification_type="backup.restore.completed",
        title="Backup restored",
        body=f"Restore {payload.get('restore_id', '')} completed successfully.",
        severity=NotificationSeverity.SUCCESS,
        metadata={"restore_id": str(payload.get("restore_id", ""))},
        outbox_event=event,
    )


def _handle_export_completed(event: OutboxEvent) -> None:
    payload = event.payload
    try:
        company = Company.objects.filter(id=UUID(str(payload.get("company_id", "")))).first()
    except ValueError:
        return
    requested_by = str(payload.get("requested_by", ""))
    try:
        user = User.objects.filter(id=UUID(requested_by)).first() if requested_by else None
    except ValueError:
        return
    if company is None or user is None:
        return
    file_name = str(payload.get("file_name", ""))
    create_notification(
        company=company,
        user=user,
        notification_type="exports.completed",
        title="Export ready",
        body=f"Export {file_name} is ready to download." if file_name else "Your export is ready to download.",
        severity=NotificationSeverity.SUCCESS,
        metadata={"file_name": file_name, "request_id": str(payload.get("request_id", ""))},
        outbox_event=event,
    )


_EVENT_HANDLERS: dict[str, Callable[[OutboxEvent], None]] = {
    "backup.completed": _handle_backup_completed,
    "backup.restore.completed": _handle_backup_restore_completed,
    "exports.completed": _handle_export_completed,
}


@transaction.atomic
def emit_for_outbox_event(event: OutboxEvent) -> None:
    handler = _EVENT_HANDLERS.get(event.event_name)
    if handler is None or Notification.objects.filter(outbox_event_id=event.id).exists():
        return
    handler(event)
    if event.published_at is None:
        OutboxEvent.objects.filter(id=event.id).update(published_at=timezone.now())


def consume_pending_outbox_events(*, limit: int = 100) -> int:
    pending = OutboxEvent.objects.filter(
        event_name__in=SUBSCRIBED_EVENT_NAMES, published_at__isnull=True
    ).order_by("occurred_at")[:limit]
    processed = 0
    for event in pending:
        emit_for_outbox_event(event)
        processed += 1
    return processed