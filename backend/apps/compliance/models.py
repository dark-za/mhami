"""Models for the compliance module.

Three surface-level artefacts live here:

* :class:`ProcessingActivity` — a ROPA row, one per documented
  processing purpose.
* :class:`DSRRequest` — a Data Subject Rights intake record, owned by
  the tenant but reachable by the platform Data Protection Officer.
* :class:`LegalDocument` — the platform-side registry of the
  published versions of the legal documents under ``docs/legal/``.
  ``apps.tenancy.models.LegalAcceptance`` references a ``LegalDocument``
  indirectly through its ``(document_type, document_version)`` pair.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.platform_core.querysets import TenantManager


class LegalBasis(models.TextChoices):
    """Enumerated lawful bases for processing personal data.

    The values mirror the documented lawful bases for the Personal Data
    Protection Law (PDPL) and the General Data Protection Regulation
    (GDPR). They are documented here so the API contract is stable
    even if external legal review re-labels a basis.
    """

    CONSENT = "consent", "Consent"
    CONTRACT = "contract", "Contract performance"
    LEGAL_OBLIGATION = "legal_obligation", "Legal obligation"
    VITAL_INTERESTS = "vital_interests", "Vital interests"
    PUBLIC_TASK = "public_task", "Public task"
    LEGITIMATE_INTERESTS = "legitimate_interests", "Legitimate interests"


class ProcessingActivity(models.Model):
    """A single ROPA entry — one row per documented processing purpose.

    The platform stores every documented processing purpose as a row in
    this table. Each row carries the controller/processor assignment,
    the categories of data and data subjects involved, the recipients,
    the retention period, the lawful basis, the cross-border transfer
    flag, and the most-recent review date.

    Rows are platform-global, not tenant-scoped: the platform is the
    processor and the ROPA describes what the platform does for every
    tenant. Tenant-specific configuration (industry, AI provider, etc.)
    is recorded separately under ``Company`` and the AI/connector
    configuration tables.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    purpose = models.TextField()
    controller = models.CharField(max_length=200)
    processor = models.CharField(max_length=200, default="Mhami Platform")
    data_categories = models.JSONField(default=list)
    data_subject_categories = models.JSONField(default=list)
    recipients = models.JSONField(default=list)
    lawful_basis = models.CharField(max_length=64, choices=LegalBasis.choices)
    cross_border_transfer = models.BooleanField(default=False)
    transfer_mechanism = models.CharField(max_length=200, blank=True)
    retention_days = models.PositiveIntegerField()
    security_measures = models.TextField()
    last_reviewed_at = models.DateField()
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["is_published", "name"]),
            models.Index(fields=["last_reviewed_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - debug only
        return self.name


class DSRRequestType(models.TextChoices):
    """Data Subject Right covered by a :class:`DSRRequest`."""

    ACCESS = "access", "Right to Access"
    RECTIFICATION = "rectification", "Right to Rectification"
    ERASURE = "erasure", "Right to Erasure"
    RESTRICTION = "restriction", "Right to Restriction"
    PORTABILITY = "portability", "Right to Portability"
    OBJECTION = "objection", "Right to Object"


class DSRRequestStatus(models.TextChoices):
    """Lifecycle status of a :class:`DSRRequest`.

    The status moves forward through the documented workflow::

        PENDING  ─►  VERIFIED  ─►  IN_PROGRESS  ─►  COMPLETED
                       │                                 │
                       └──────────── REJECTED ──────────┘

    ``REJECTED`` is reachable from any of the prior states; the
    decision is recorded in the audit log with the rejection reason.
    """

    PENDING = "pending", "Pending"
    VERIFIED = "verified", "Identity Verified"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    REJECTED = "rejected", "Rejected"


class DSRRequest(models.Model):
    """A Data Subject Rights request.

    A row is created when a data subject (typically an employee or
    owner) submits a request through the public DSR endpoint. The
    request is owned by the tenant ``Company`` so that the company
    can see and decide it; the platform DPO is also notified through
    the audit log.

    The platform records only the minimum data subject identifier
    needed to action the request (typically a corporate email).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "tenancy.Company",
        on_delete=models.CASCADE,
        related_name="dsr_requests",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="dsr_requests",
        null=True,
        blank=True,
    )
    request_type = models.CharField(max_length=32, choices=DSRRequestType.choices)
    subject_email = models.EmailField()
    subject_reference = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    verification_token_hash = models.CharField(max_length=64, blank=True)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_attempts = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=32, choices=DSRRequestStatus.choices, default=DSRRequestStatus.PENDING)
    decision_notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="dsr_decisions",
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        ordering = ("-submitted_at",)
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["status", "submitted_at"]),
        ]


class LegalDocumentKind(models.TextChoices):
    """Enumerated document kinds for the :class:`LegalDocument` registry.

    The values mirror ``apps.tenancy.models.LegalDocumentType`` for the
    four documents that require per-tenant acceptance. Bundle documents
    (Terms, Data Processing, Retention, Support Access) are tracked
    here as well so the platform has a single source of truth for what
    is currently published.
    """

    TERMS = "terms", "Terms of Use"
    PRIVACY = "privacy", "Privacy Notice"
    AI_TRANSFER = "ai_transfer", "AI Transfer Notice"
    EMPLOYEE_PRIVACY = "employee_privacy", "Employee Privacy Acknowledgement"
    DATA_PROCESSING = "data_processing", "Data Processing Terms"
    RETENTION = "retention", "Retention and Deletion Policy"
    SUPPORT_ACCESS = "support_access", "Support Access Authorization"
    DPIA = "dpia", "Data Protection Impact Assessment"
    BREACH_RESPONSE = "breach_response", "Data Breach Response Plan"
    ROPA = "ropa", "Record of Processing Activities"


class LegalDocument(models.Model):
    """A published version of a legal document.

    The platform-side registry for every legal artefact under
    ``docs/legal/``. The ``(kind, version)`` pair is unique. The
    ``content_path`` field points at the in-tree file path; the
    ``summary`` field carries a short human-readable abstract used by
    the API. Content is intentionally not duplicated into the
    database; the document is the file.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=64, choices=LegalDocumentKind.choices)
    version = models.CharField(max_length=64)
    content_path = models.CharField(max_length=500)
    summary = models.CharField(max_length=500, blank=True)
    effective_date = models.DateField()
    supersedes_version = models.CharField(max_length=64, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_legal_documents",
    )
    published_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("kind", "version"),
                name="compliance_legal_document_unique_version",
            ),
            models.UniqueConstraint(
                fields=("kind", "is_current"),
                condition=models.Q(is_current=True),
                name="compliance_legal_document_single_current",
            ),
        ]
        indexes = [
            models.Index(fields=["kind", "effective_date"]),
        ]
        ordering = ("kind", "-effective_date")

    def __str__(self) -> str:  # pragma: no cover - debug only
        return f"{self.kind}@{self.version}"
