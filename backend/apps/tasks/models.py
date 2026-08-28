from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.organizations.models import Branch
from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class TaskRiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class TaskAssignmentMode(models.TextChoices):
    NAMED_USER = "named_user", "Named User"
    ROLE_POOL = "role_pool", "Role Pool"
    MONITOR_DISTRIBUTED = "monitor_distributed", "Monitor Distributed"


class TaskRecurrenceType(models.TextChoices):
    DAILY_FIXED = "daily_fixed", "Daily Fixed"
    WEEKLY_FIXED = "weekly_fixed", "Weekly Fixed"
    SHIFT_RELATIVE = "shift_relative", "Shift Relative"


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CLAIMED = "claimed", "Claimed"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    OVERDUE = "overdue", "Overdue"


class TaskTransferStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class TaskTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task_templates")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="task_templates", null=True, blank=True)
    slug = models.SlugField(max_length=96)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignment_mode = models.CharField(max_length=32, choices=TaskAssignmentMode.choices)
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_task_templates",
        null=True,
        blank=True,
    )
    assigned_role_code = models.CharField(max_length=64, blank=True)
    risk_level = models.CharField(max_length=32, choices=TaskRiskLevel.choices, default=TaskRiskLevel.LOW)
    task_weight = models.PositiveSmallIntegerField(default=1)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "slug"], name="tasks_template_unique_slug")]


class TaskTemplateVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(TaskTemplate, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    instructions = models.TextField()
    checklist_definition = models.JSONField(default=list)
    evidence_requirements = models.JSONField(default=list)
    reference_instructions = models.TextField(blank=True)
    risk_level = models.CharField(max_length=32, choices=TaskRiskLevel.choices, default=TaskRiskLevel.LOW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["template", "version_number"], name="tasks_template_version_unique"),
        ]


class TaskSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task_schedules")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="task_schedules", null=True, blank=True)
    template = models.ForeignKey(TaskTemplate, on_delete=models.CASCADE, related_name="schedules")
    recurrence_type = models.CharField(max_length=32, choices=TaskRecurrenceType.choices)
    scheduled_time = models.TimeField(null=True, blank=True)
    weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    shift_offset_minutes = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    last_generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "template", "branch", "recurrence_type", "weekday", "scheduled_time"],
                name="tasks_schedule_unique",
            ),
        ]


class TaskInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task_instances")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="task_instances")
    template = models.ForeignKey(TaskTemplate, on_delete=models.PROTECT, related_name="instances")
    template_version = models.ForeignKey(TaskTemplateVersion, on_delete=models.PROTECT, related_name="instances")
    schedule = models.ForeignKey(TaskSchedule, on_delete=models.SET_NULL, related_name="instances", null=True, blank=True)
    scheduled_for = models.DateTimeField()
    due_at = models.DateTimeField()
    status = models.CharField(max_length=32, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="task_instances",
        null=True,
        blank=True,
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="claimed_task_instances",
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    overdue_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["schedule", "scheduled_for"], name="tasks_instance_schedule_unique"),
        ]


class TaskTransferRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_instance = models.ForeignKey(TaskInstance, on_delete=models.CASCADE, related_name="transfer_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="task_transfer_requests")
    requested_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="task_transfer_targets",
    )
    status = models.CharField(max_length=32, choices=TaskTransferStatus.choices, default=TaskTransferStatus.PENDING)
    reason = models.CharField(max_length=255, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="task_transfer_decisions",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
