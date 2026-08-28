from __future__ import annotations

from celery import shared_task

from .services import process_lifecycle_expirations


@shared_task(name="apps.tenancy.process_lifecycle_expirations")
def process_lifecycle_expirations_task() -> dict[str, int]:
    return process_lifecycle_expirations()
