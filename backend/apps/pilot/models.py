from __future__ import annotations

import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.db import models

from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class PilotProgram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="pilot_program")
    status = models.CharField(max_length=32, default="planned")
    branch_count_target = models.PositiveSmallIntegerField(default=3)
    employee_count_target = models.PositiveSmallIntegerField(default=30)
    chrome_device_count = models.PositiveSmallIntegerField(default=1)
    ai_provider_name = models.CharField(max_length=64, blank=True)
    connector_owner = models.CharField(max_length=255, blank=True)
    test_environment = models.CharField(max_length=255, blank=True)
    success_measures = models.JSONField(default=list)
    escalation_contacts = models.JSONField(default=list)
    operating_checklist = models.JSONField(default=list)
    weekly_metrics_goal = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="pilot_program_updates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()


class PilotWeeklyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="weekly_reports")
    week_ending = models.DateField()
    metrics = models.JSONField(default=dict)
    ai_agreement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    error_analysis = models.TextField(blank=True)
    capacity_findings = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pilot_weekly_reports")
    created_at = models.DateTimeField(auto_now_add=True)


class PilotIssue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="issues")
    title = models.CharField(max_length=255)
    severity = models.CharField(max_length=32, default="medium")
    status = models.CharField(max_length=32, default="open")
    details = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pilot_issues")
    created_at = models.DateTimeField(auto_now_add=True)


class PilotChangeRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="change_requests")
    title = models.CharField(max_length=255)
    rationale = models.TextField(blank=True)
    status = models.CharField(max_length=32, default="requested")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="pilot_change_approvals")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pilot_change_requests")
    created_at = models.DateTimeField(auto_now_add=True)


class PilotCharter(models.Model):
    """PILOT-01: signed pilot charter.

    Mirrors the :class:`ExitDecision` HMAC pattern so a tampered charter
    fails ``verify_signature``. There can be multiple charters per
    ``PilotProgram`` (e.g. withdraw + re-authorize); ``latest_charter``
    returns the most recent one.
    """

    class Decision(models.TextChoices):
        AUTHORIZE = "authorize", "Authorize"
        DECLINE = "decline", "Decline"
        WITHDRAW = "withdraw", "Withdraw"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="charters")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="pilot_charters")
    decision = models.CharField(max_length=16, choices=Decision.choices)
    rationale = models.TextField()
    conditions = models.TextField(blank=True)
    observation_start = models.DateField(null=True, blank=True)
    observation_end = models.DateField(null=True, blank=True)
    success_measures = models.JSONField(default=list)
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pilot_charters"
    )
    signed_at = models.DateTimeField(auto_now_add=True)
    signature_hmac = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["company", "signed_at"], name="pilot_charter_co_sa_idx"),
            models.Index(fields=["pilot_program", "signed_at"], name="pilot_charter_pp_sa_idx"),
        ]

    objects = TenantManager()

    def _canonical_payload(self) -> bytes:
        payload = {
            "id": str(self.id),
            "pilot_program": str(self.pilot_program_id),
            "company": str(self.company_id),
            "decision": self.decision,
            "rationale": self.rationale,
            "conditions": self.conditions,
            "observation_start": self.observation_start.isoformat() if self.observation_start else "",
            "observation_end": self.observation_end.isoformat() if self.observation_end else "",
            "success_measures": list(self.success_measures or []),
            "signed_by": str(self.signed_by_id),
            "signed_at": self.signed_at.isoformat() if self.signed_at else "",
            "metadata": dict(self.metadata or {}),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")

    def compute_signature(self) -> str:
        secret = str(getattr(settings, "AUDIT_HMAC_SECRET", settings.SECRET_KEY)).encode("utf-8")
        return hmac.new(secret, self._canonical_payload(), hashlib.sha256).hexdigest()

    def verify_signature(self) -> bool:
        if not self.signature_hmac:
            return False
        return hmac.compare_digest(self.signature_hmac, self.compute_signature())
