from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class ExportType(models.TextChoices):
    CSV = "csv", "CSV"
    ZIP = "zip", "ZIP"
    PDF = "pdf", "PDF"


class ExportStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    EXPIRED = "expired", "Expired"


class ExportBoundaryPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="export_policy")
    future_notification_boundaries = models.JSONField(default=list)
    external_storage_boundaries = models.JSONField(default=list)
    provider_review_checklist = models.JSONField(default=list)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="export_policy_updates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()


class ExportRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="export_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="export_requests")
    export_type = models.CharField(max_length=32, choices=ExportType.choices)
    branch_ids = models.JSONField(default=list)
    categories = models.JSONField(default=list)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=ExportStatus.choices, default=ExportStatus.QUEUED)
    download_token = models.CharField(max_length=128, unique=True)
    file_name = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()
