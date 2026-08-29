from __future__ import annotations

import hashlib
import json
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.tenancy.models import Company


class AgentScope(models.TextChoices):
    READ_TASKS = "read:tasks", "Read tasks"
    READ_REPORTS = "read:reports", "Read reports"
    WRITE_TASKS_TRANSFER = "write:tasks:transfer", "Transfer tasks"
    WRITE_REVIEWS_APPROVE = "write:reviews:approve", "Approve reviews"
    ADMIN_FULL = "admin:full", "Full administration"


AGENT_SCOPE_VALUES: frozenset[str] = frozenset(
    {
        "read:tasks",
        "read:reports",
        "write:tasks:transfer",
        "write:reviews:approve",
        "admin:full",
    }
)
DEPRECATED_AGENT_SCOPES: frozenset[str] = frozenset()


def active_agent_scope_values() -> set[str]:
    return set(AGENT_SCOPE_VALUES - DEPRECATED_AGENT_SCOPES)


def validate_agent_scopes(scopes: list[str]) -> None:
    unknown = sorted(set(scopes) - AGENT_SCOPE_VALUES)
    if unknown:
        raise ValidationError({"scopes": f"Unknown agent scope(s): {', '.join(unknown)}"})


def arguments_hash(arguments: dict[str, object]) -> str:
    payload = json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AgentGrantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


class AgentActionStatus(models.TextChoices):
    RECEIVED = "received", "Received"
    EXECUTED = "executed", "Executed"
    REJECTED = "rejected", "Rejected"
    FAILED = "failed", "Failed"


class AgentPendingActionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    EXECUTING = "executing", "Executing"
    EXECUTED = "executed", "Executed"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"
    SUPERSEDED = "superseded", "Superseded"
    FAILED = "failed", "Failed"


class AgentGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="agent_grants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="agent_grants")
    client_name = models.CharField(max_length=160)
    client_fingerprint = models.CharField(max_length=128)
    scopes = models.JSONField(default=list)
    status = models.CharField(max_length=32, choices=AgentGrantStatus.choices, default=AgentGrantStatus.ACTIVE)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["client_fingerprint", "status"]),
        ]

    def clean(self) -> None:
        if not isinstance(self.scopes, list) or not all(isinstance(scope, str) for scope in self.scopes):
            raise ValidationError({"scopes": "Agent scopes must be a list of strings."})
        validate_agent_scopes(self.scopes)

    @property
    def active(self) -> bool:
        return self.status == AgentGrantStatus.ACTIVE and self.revoked_at is None and self.expires_at > timezone.now()


class AgentActionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant = models.ForeignKey(AgentGrant, on_delete=models.PROTECT, related_name="action_logs")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="agent_action_logs")
    request_id = models.UUIDField(db_index=True)
    tool_name = models.CharField(max_length=160)
    required_scope = models.CharField(max_length=96)
    idempotency_key = models.CharField(max_length=160)
    arguments_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=32, choices=AgentActionStatus.choices, default=AgentActionStatus.RECEIVED)
    result = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=96, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["grant", "tool_name", "idempotency_key"],
                name="agent_action_unique_idempotency_key",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "created_at"]),
            models.Index(fields=["tool_name", "status"]),
        ]

    def clean(self) -> None:
        validate_agent_scopes([self.required_scope])


class AgentPendingAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant = models.ForeignKey(AgentGrant, on_delete=models.PROTECT, related_name="pending_actions")
    action_log = models.ForeignKey(
        AgentActionLog,
        on_delete=models.PROTECT,
        related_name="pending_actions",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=32,
        choices=AgentPendingActionStatus.choices,
        default=AgentPendingActionStatus.PENDING,
    )
    action_type = models.CharField(max_length=160)
    payload = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="agent_pending_action_decisions",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    terminal_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["grant", "status"]),
            models.Index(fields=["expires_at", "status"]),
        ]
