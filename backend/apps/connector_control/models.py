from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class ConnectorStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"
    OUTDATED = "outdated", "Outdated"


class ConnectorHealthStatus(models.TextChoices):
    HEALTHY = "healthy", "Healthy"
    DEGRADED = "degraded", "Degraded"
    OFFLINE = "offline", "Offline"


class TenantConnectorEnrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="connector_enrollment")
    connector_version = models.CharField(max_length=64)
    compatibility_window = models.CharField(max_length=64, default=">=0.1,<1.0")
    status = models.CharField(max_length=32, choices=ConnectorStatus.choices, default=ConnectorStatus.PENDING)
    health_status = models.CharField(max_length=32, choices=ConnectorHealthStatus.choices, default=ConnectorHealthStatus.OFFLINE)
    shared_secret_fingerprint = models.CharField(max_length=128, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    health_expires_at = models.DateTimeField(null=True, blank=True)
    health_ttl_seconds = models.PositiveIntegerField(default=300)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="connector_enrollments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()
