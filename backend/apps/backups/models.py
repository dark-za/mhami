from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class BackupStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    RESTORED = "restored", "Restored"


class BackupPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="backup_policy")
    destination_name = models.CharField(max_length=255, default="secondary")
    encrypted = models.BooleanField(default=False)
    schedule_cron = models.CharField(max_length=64, default="0 2 * * *")
    rpo_hours = models.PositiveSmallIntegerField(default=24)
    rto_hours = models.PositiveSmallIntegerField(default=24)
    includes_private_media = models.BooleanField(default=True)
    includes_configuration = models.BooleanField(default=True)
    includes_tenant_state = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="backup_policy_updates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()


class BackupRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="backup_runs")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="backup_runs")
    status = models.CharField(max_length=32, choices=BackupStatus.choices, default=BackupStatus.REQUESTED)
    artifact_name = models.CharField(max_length=255, blank=True)
    artifact_sha256 = models.CharField(max_length=64, blank=True)
    manifest_sha256 = models.CharField(max_length=64, blank=True)
    manifest = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    restored_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()


class RestoreRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="restore_runs")
    backup_run = models.ForeignKey(BackupRun, on_delete=models.CASCADE, related_name="restore_runs")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="restore_runs")
    status = models.CharField(max_length=32, choices=BackupStatus.choices, default=BackupStatus.REQUESTED)
    verified_database = models.BooleanField(default=False)
    verified_media = models.BooleanField(default=False)
    verified_configuration = models.BooleanField(default=False)
    target_name = models.CharField(max_length=64, blank=True)
    report = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()
