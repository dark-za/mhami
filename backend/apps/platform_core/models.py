from __future__ import annotations

import hashlib
import hmac
import uuid

from django.conf import settings
from django.db import models


class PlatformSetting(models.Model):
    key = models.CharField(max_length=200, unique=True)
    value = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeatureFlag(models.Model):
    key = models.CharField(max_length=200)
    enabled = models.BooleanField(default=False)
    scope = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key", "scope"], name="platform_feature_flag_unique_scope"),
        ]


class OutboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(max_length=200)
    aggregate_type = models.CharField(max_length=200)
    aggregate_id = models.CharField(max_length=200)
    payload = models.JSONField(default=dict)
    request_id = models.UUIDField(default=uuid.uuid4)
    occurred_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["event_name", "occurred_at"]),
            models.Index(fields=["published_at", "occurred_at"]),
        ]


class ModuleHealthSnapshot(models.Model):
    module_slug = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=20)
    details = models.JSONField(default=dict)
    checked_at = models.DateTimeField(auto_now=True)


class ExitDecision(models.Model):
    """Records a platform-owner's binding decision on a phase exit dossier.

    C-06: decisions are immutable once signed. A revocation creates a new
    decision that supersedes the previous one. Each decision is captured
    in the audit chain and carries an HMAC of the canonical payload so
    tampering with the rationale invalidates the signature.
    """

    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        CONDITIONAL = "conditional", "Conditional approval"
        REJECTED = "rejected", "Rejected"
        DEFERRED = "deferred", "Deferred"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase = models.CharField(max_length=16)
    decision = models.CharField(max_length=16, choices=Decision.choices)
    rationale = models.TextField()
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="exit_decisions"
    )
    signed_at = models.DateTimeField(auto_now_add=True)
    supersedes = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="superseded_by",
    )
    signature_hmac = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["phase", "signed_at"], name="platform_co_phase__idx"),
            models.Index(fields=["phase", "decision"], name="platform_co_phase__dec_idx"),
        ]

    def _canonical_payload(self) -> bytes:
        import json

        payload = {
            "id": str(self.id),
            "phase": self.phase,
            "decision": self.decision,
            "rationale": self.rationale,
            "signed_by": str(self.signed_by_id),
            "signed_at": self.signed_at.isoformat(),
            "supersedes": str(self.supersedes_id) if self.supersedes_id else "",
            "metadata": self.metadata,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")

    def compute_signature(self) -> str:
        secret = str(getattr(settings, "AUDIT_HMAC_SECRET", settings.SECRET_KEY)).encode("utf-8")
        return hmac.new(secret, self._canonical_payload(), hashlib.sha256).hexdigest()

    def verify_signature(self) -> bool:
        if not self.signature_hmac:
            return False
        expected = self.compute_signature()
        return hmac.compare_digest(self.signature_hmac, expected)
