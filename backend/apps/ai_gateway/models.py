from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.evidence.models import EvidenceItem
from apps.organizations.models import Branch
from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class AIAnalysisStatus(models.TextChoices):
    COMPLETED = "completed", "Completed"
    NEEDS_REVIEW = "needs_review", "Needs Review"
    FAILED = "failed", "Failed"


class AIProviderConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="ai_provider_config")
    provider_name = models.CharField(max_length=64, default="fake")
    endpoint_url = models.CharField(max_length=255, blank=True)
    model_name = models.CharField(max_length=128, blank=True)
    credential_reference = models.CharField(max_length=255, blank=True)
    monthly_token_limit = models.PositiveIntegerField(default=10000)
    monthly_cost_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    enabled = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="ai_provider_updates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()


class AIAnalysisCriterion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ai_analysis_criteria")
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    criteria_json = models.JSONField(default=dict)
    reference_media_names = models.JSONField(default=list)
    shadow_mode = models.BooleanField(default=True)
    auto_pass_enabled = models.BooleanField(default=False)
    auto_pass_risk_threshold = models.PositiveSmallIntegerField(default=70)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ai_analysis_criteria")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "version_number"], name="ai_analysis_criteria_version_unique"),
            models.CheckConstraint(
                condition=models.Q(shadow_mode=True) & models.Q(auto_pass_enabled=False),
                name="ai_criteria_shadow_no_auto_pass",
            ),
        ]


class AIAnalysisRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ai_analysis_runs")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="ai_analysis_runs")
    evidence_item = models.ForeignKey(EvidenceItem, on_delete=models.CASCADE, null=True, blank=True, related_name="ai_analysis_runs")
    provider_name = models.CharField(max_length=64)
    model_name = models.CharField(max_length=128, blank=True)
    prompt_version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=32, choices=AIAnalysisStatus.choices, default=AIAnalysisStatus.COMPLETED)
    shadow_mode = models.BooleanField(default=True)
    auto_pass_eligible = models.BooleanField(default=False)
    auto_pass_activated = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=32, blank=True)
    provider_payload = models.JSONField(default=dict)
    provider_result = models.JSONField(default=dict)
    human_decision = models.CharField(max_length=32, blank=True)
    agreement_with_human = models.BooleanField(null=True, blank=True)
    review_decision = models.ForeignKey(
        "reviews.ReviewDecision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_analysis_runs",
    )
    error_message = models.CharField(max_length=255, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ai_analysis_runs")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(shadow_mode=True) & models.Q(auto_pass_activated=False),
                name="ai_run_shadow_no_auto_pass",
            )
        ]
