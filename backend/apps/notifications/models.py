from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class NotificationSeverity(models.TextChoices):
    INFO = "info", "Info"
    SUCCESS = "success", "Success"
    WARNING = "warning", "Warning"
    DANGER = "danger", "Danger"


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="notifications")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=120)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    severity = models.CharField(max_length=16, choices=NotificationSeverity.choices, default=NotificationSeverity.INFO)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    outbox_event = models.OneToOneField(
        "platform_core.OutboxEvent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        indexes = [
            models.Index(fields=["company", "user", "-created_at"]),
            models.Index(fields=["user", "read_at"]),
        ]