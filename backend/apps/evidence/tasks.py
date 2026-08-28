from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from .models import CaptureSession, CaptureSessionStatus


@shared_task(name="apps.evidence.cleanup_expired_sessions")
def cleanup_expired_sessions() -> int:
    expired = CaptureSession.objects.filter(status=CaptureSessionStatus.ACTIVE, expires_at__lt=timezone.now()).update(
        status=CaptureSessionStatus.EXPIRED
    )
    return expired
