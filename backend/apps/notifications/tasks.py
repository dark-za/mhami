from __future__ import annotations

from celery import shared_task

from .services import consume_pending_outbox_events


@shared_task(name="apps.notifications.process_outbox_events")
def process_outbox_events() -> int:
    return consume_pending_outbox_events()