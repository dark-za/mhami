from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.evidence.models import EvidenceItem, TaskIssueReport
from apps.organizations.models import Branch
from apps.platform_core.querysets import TenantManager
from apps.tasks.models import TaskInstance
from apps.tenancy.models import Company


class ReviewDecisionType(models.TextChoices):
    APPROVE = "approve", "Approve"
    APPROVE_DESPITE_ALERT = "approve_despite_alert", "Approve Despite Alert"
    RETRY_SAME_TASK = "retry_same_task", "Retry Same Task"
    MARK_MISSED = "mark_missed", "Mark Missed"
    CREATE_CORRECTIVE_TASK = "create_corrective_task", "Create Corrective Task"
    CANCEL = "cancel", "Cancel"
    OVERRIDE_RESTRICTION = "override_restriction", "Override Restriction"


class ReviewPolicySetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="review_policy")
    employee_score_visibility = models.CharField(max_length=32, default="summary")
    historical_report_restatement = models.BooleanField(default=False)
    monitor_approval_required = models.BooleanField(default=True)
    sensitive_task_claim_restricted = models.BooleanField(default=True)
    extra_evidence_required = models.BooleanField(default=False)
    owner_alerts_enabled = models.BooleanField(default=True)
    approved_task_weight_cap = models.PositiveSmallIntegerField(default=5)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="review_policy_updates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()


class ReviewDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="review_decisions")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="review_decisions")
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="review_decisions")
    decision_type = models.CharField(max_length=32, choices=ReviewDecisionType.choices)
    reason = models.CharField(max_length=255, blank=True)
    task_instance = models.ForeignKey(TaskInstance, on_delete=models.CASCADE, null=True, blank=True, related_name="review_decisions")
    evidence_item = models.ForeignKey(EvidenceItem, on_delete=models.CASCADE, null=True, blank=True, related_name="review_decisions")
    issue_report = models.ForeignKey(TaskIssueReport, on_delete=models.CASCADE, null=True, blank=True, related_name="review_decisions")
    generated_task_instance = models.ForeignKey(TaskInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_by_review_decisions")
    restriction_name = models.CharField(max_length=128, blank=True)
    original_status = models.CharField(max_length=32, blank=True)
    resulting_status = models.CharField(max_length=32, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()
