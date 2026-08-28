from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.organizations.models import Branch
from apps.platform_core.querysets import TenantManager
from apps.tasks.models import TaskInstance, TaskTemplateVersion
from apps.tenancy.models import Company


class EvidenceType(models.TextChoices):
    IMAGE = "image", "Image"
    NUMBER = "number", "Number"
    NOTE = "note", "Note"
    CONFIRMATION = "confirmation", "Confirmation"


class CaptureSessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    USED = "used", "Used"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class EvidenceStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    NEEDS_REVIEW = "needs_review", "Needs Review"
    REJECTED = "rejected", "Rejected"


class CaptureSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="capture_sessions")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="capture_sessions")
    task_instance = models.ForeignKey(TaskInstance, on_delete=models.CASCADE, related_name="capture_sessions")
    template_version = models.ForeignKey(TaskTemplateVersion, on_delete=models.PROTECT, related_name="capture_sessions")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="capture_sessions")
    evidence_type = models.CharField(max_length=32, choices=EvidenceType.choices)
    token = models.CharField(max_length=128, unique=True)
    challenge_text = models.CharField(max_length=255, blank=True)
    challenge_answer = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=CaptureSessionStatus.choices, default=CaptureSessionStatus.ACTIVE)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="used_capture_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()


class EvidenceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="evidence_items")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="evidence_items")
    task_instance = models.ForeignKey(TaskInstance, on_delete=models.CASCADE, related_name="evidence_items")
    capture_session = models.ForeignKey(CaptureSession, on_delete=models.PROTECT, related_name="evidence_items")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evidence_items")
    evidence_type = models.CharField(max_length=32, choices=EvidenceType.choices)
    status = models.CharField(max_length=32, choices=EvidenceStatus.choices, default=EvidenceStatus.SUBMITTED)
    sequence_number = models.PositiveIntegerField(default=1)
    parent_submission = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="retries",
    )
    note_text = models.TextField(blank=True)
    number_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    confirmation_value = models.BooleanField(null=True, blank=True)
    quarantine_name = models.CharField(max_length=255, blank=True)
    private_media_name = models.CharField(max_length=255, blank=True)
    blurred_media_name = models.CharField(max_length=255, blank=True)
    media_mime_type = models.CharField(max_length=120, blank=True)
    media_size_bytes = models.PositiveIntegerField(default=0)
    media_width = models.PositiveIntegerField(null=True, blank=True)
    media_height = models.PositiveIntegerField(null=True, blank=True)
    raw_hash = models.CharField(max_length=64, blank=True)
    derivative_hash = models.CharField(max_length=64, blank=True)
    duplicate_risk_score = models.PositiveSmallIntegerField(default=0)
    face_detected = models.BooleanField(default=False)
    challenge_response = models.CharField(max_length=255, blank=True)
    # C-13: the client flag is informational. The server records its
    # own privacy decision so the client cannot authorise an unblurred
    # image by setting ``face_detected=False``.
    privacy_decision = models.CharField(
        max_length=32,
        choices=[
            ("approved_blurred", "Approved blurred"),
            ("retained_unblurred", "Retained unblurred"),
            ("rejected_no_face", "Rejected - no face"),
            ("pending_review", "Pending review"),
            ("failed_detector", "Detector failed"),
        ],
        default="pending_review",
    )
    face_detector_version = models.CharField(max_length=32, blank=True)
    face_detector_confidence = models.PositiveSmallIntegerField(default=0)
    face_detector_raw_score = models.JSONField(default=dict)
    privacy_metadata = models.JSONField(default=dict)
    challenge_response = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["capture_session"], name="evidence_one_item_per_session"),
            models.UniqueConstraint(fields=["task_instance", "sequence_number"], name="evidence_sequence_unique_per_task"),
        ]

    @property
    def is_face_protected(self) -> bool:
        """True if the stored private media is already face-protected.

        The platform default is "approve only if blurred" so the
        privacy decision is the single source of truth; the boolean
        helper exists for readability at call sites.
        """
        return self.privacy_decision in {"approved_blurred", "rejected_no_face"}


class TaskIssueReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task_issue_reports")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="task_issue_reports")
    task_instance = models.ForeignKey(TaskInstance, on_delete=models.CASCADE, related_name="issue_reports")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="task_issue_reports")
    note = models.TextField()
    photo_name = models.CharField(max_length=255, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()


class TaskDiscussionMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="task_discussion_messages")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="task_discussion_messages")
    task_instance = models.ForeignKey(TaskInstance, on_delete=models.CASCADE, related_name="discussion_messages")
    issue_report = models.ForeignKey(TaskIssueReport, on_delete=models.CASCADE, null=True, blank=True, related_name="messages")
    reply_to = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="task_discussion_messages")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()
