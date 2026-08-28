"""Service layer for the compliance module.

The service functions in this module are the single authoritative
source of business rules for:

* Publishing and reviewing ROPA entries.
* Submitting, verifying, deciding, and rejecting Data Subject Rights
  requests.
* Publishing, superseding, and querying legal-document versions.

Every write path is wrapped in a database transaction and emits an
audit event through :mod:`apps.audit.services` so the chain is
preserved.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import date
from pathlib import Path
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.identity.models import User
from apps.tenancy.models import Company

from .models import (
    DSRRequest,
    DSRRequestStatus,
    DSRRequestType,
    LegalBasis,
    LegalDocument,
    LegalDocumentKind,
    ProcessingActivity,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
"""Filesystem path to the repository root.

Used to resolve legal-document content paths under ``docs/legal/`` so
the platform can locate a published artefact without storing the full
body in the database.
"""


class ComplianceError(ValueError):
    """Base class for compliance service errors."""


class DSRError(ComplianceError):
    """Raised for invalid Data Subject Rights transitions."""


class DocumentVersionError(ComplianceError):
    """Raised for invalid legal-document version transitions."""


def issue_dsr_verification_token(request: DSRRequest) -> str:
    """Create a one-time verification token for a pending DSR request.

    Only the SHA-256 digest is persisted. The raw token is returned once
    to the caller so it can be placed in the verification email; it is
    never stored in the database or audit metadata.
    """
    if request.status != DSRRequestStatus.PENDING:
        raise DSRError("Only pending DSR requests can be verified by email.")
    token = secrets.token_urlsafe(32)
    request.verification_token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    request.verification_sent_at = timezone.now()
    request.verification_attempts = 0
    request.save(update_fields=["verification_token_hash", "verification_sent_at", "verification_attempts", "updated_at"])
    return token


@transaction.atomic
def verify_dsr_email(request: DSRRequest, *, token: str, actor_id: str = "email") -> DSRRequest:
    """Verify a DSR email token and move the request to ``VERIFIED``.

    Tokens are single-use: the digest is cleared after successful
    verification. Failed attempts are counted and the request is
    rejected after five invalid attempts.
    """
    if request.status != DSRRequestStatus.PENDING or not request.verification_token_hash:
        raise DSRError("This DSR verification link is invalid or expired.")
    digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    if not secrets.compare_digest(digest, request.verification_token_hash):
        request.verification_attempts += 1
        request.save(update_fields=["verification_attempts", "updated_at"])
        raise DSRError("This DSR verification link is invalid or expired.")
    request.verified_at = timezone.now()
    request.verification_token_hash = ""
    request.save(update_fields=["verified_at", "verification_token_hash", "updated_at"])
    return _transition_dsr(request, target=str(DSRRequestStatus.VERIFIED), actor_id=actor_id, notes="Email verified.")


# ---------------------------------------------------------------------------
# ROPA — ProcessingActivity
# ---------------------------------------------------------------------------


@transaction.atomic
def publish_processing_activity(
    *,
    name: str,
    purpose: str,
    controller: str,
    data_categories: Iterable[str],
    data_subject_categories: Iterable[str],
    recipients: Iterable[str],
    lawful_basis: str,
    retention_days: int,
    security_measures: str,
    cross_border_transfer: bool = False,
    transfer_mechanism: str = "",
    processor: str = "Mhami Platform",
    last_reviewed_at: date | None = None,
    actor_id: str | None = None,
) -> ProcessingActivity:
    """Create or update a :class:`ProcessingActivity` and publish it.

    A row is upserted by ``name``. The first call for a given name
    creates the row with ``is_published=True``; subsequent calls
    update the row in place and emit an audit event.

    Args:
        name: Unique processing-activity name (the ROPA key).
        purpose: Plain-language statement of the purpose.
        controller: The legal controller (the tenant company, by default).
        data_categories: Iterable of personal-data categories processed.
        data_subject_categories: Iterable of data subject categories.
        recipients: Iterable of recipient categories.
        lawful_basis: One of :class:`LegalBasis` values.
        retention_days: Retention window in days.
        security_measures: Plain-language description of measures.
        cross_border_transfer: Whether the activity crosses borders.
        transfer_mechanism: Documentation of the transfer mechanism
            (e.g. SCC reference) when ``cross_border_transfer`` is true.
        processor: The processor label, defaults to the platform.
        last_reviewed_at: Date of the latest review; defaults to today.
        actor_id: Audit actor id; defaults to ``"system"``.

    Returns:
        The created or updated :class:`ProcessingActivity`.
    """
    if lawful_basis not in LegalBasis.values:
        raise ComplianceError(f"Unknown lawful_basis: {lawful_basis!r}")
    if retention_days <= 0:
        raise ComplianceError("retention_days must be positive.")
    if cross_border_transfer and not transfer_mechanism.strip():
        raise ComplianceError("cross_border_transfer requires a transfer_mechanism.")

    last_reviewed_at = last_reviewed_at or timezone.now().date()
    activity, created = ProcessingActivity.objects.update_or_create(
        name=name,
        defaults={
            "purpose": purpose,
            "controller": controller,
            "processor": processor,
            "data_categories": list(data_categories),
            "data_subject_categories": list(data_subject_categories),
            "recipients": list(recipients),
            "lawful_basis": lawful_basis,
            "cross_border_transfer": cross_border_transfer,
            "transfer_mechanism": transfer_mechanism,
            "retention_days": retention_days,
            "security_measures": security_measures,
            "last_reviewed_at": last_reviewed_at,
            "is_published": True,
            "published_at": timezone.now(),
        },
    )
    record_audit_event(
        event_type="compliance.ropa.published",
        target_type="processing_activity",
        target_id=str(activity.id),
        actor_id=actor_id or "system",
        metadata={
            "name": activity.name,
            "lawful_basis": activity.lawful_basis,
            "retention_days": activity.retention_days,
            "created": created,
        },
    )
    return activity


def list_published_activities() -> list[ProcessingActivity]:
    """Return all currently published ROPA rows, ordered by name."""
    return list(ProcessingActivity.objects.filter(is_published=True).order_by("name"))


# ---------------------------------------------------------------------------
# DSR — DataSubjectRights
# ---------------------------------------------------------------------------


_ALLOWED_DSR_TRANSITIONS: dict[str, set[str]] = {
    str(DSRRequestStatus.PENDING): {str(DSRRequestStatus.VERIFIED), str(DSRRequestStatus.REJECTED)},
    str(DSRRequestStatus.VERIFIED): {str(DSRRequestStatus.IN_PROGRESS), str(DSRRequestStatus.REJECTED)},
    str(DSRRequestStatus.IN_PROGRESS): {str(DSRRequestStatus.COMPLETED), str(DSRRequestStatus.REJECTED)},
    str(DSRRequestStatus.COMPLETED): set(),
    str(DSRRequestStatus.REJECTED): set(),
}


@transaction.atomic
def submit_dsr_request(
    *,
    company: Company,
    request_type: str,
    subject_email: str,
    subject_reference: str = "",
    description: str = "",
    submitted_by: User | None = None,
) -> DSRRequest:
    """Create a new :class:`DSRRequest` for a tenant.

    The request is created in the :attr:`DSRRequestStatus.PENDING`
    state. Identity verification happens through
    :func:`verify_dsr_identity`.

    Args:
        company: The tenant that the request is filed against.
        request_type: One of :class:`DSRRequestType` values.
        subject_email: The data subject's email address.
        subject_reference: Optional employee reference for cross-checking.
        description: Free-form description of the request.
        submitted_by: Authenticated user filing the request, if any.

    Returns:
        The created :class:`DSRRequest`.
    """
    if request_type not in DSRRequestType.values:
        raise DSRError(f"Unknown request_type: {request_type!r}")
    dsr = DSRRequest.objects.create(
        company=company,
        submitted_by=submitted_by,
        request_type=request_type,
        subject_email=subject_email,
        subject_reference=subject_reference,
        description=description,
    )
    record_audit_event(
        event_type="compliance.dsr.submitted",
        target_type="dsr_request",
        target_id=str(dsr.id),
        actor_id=str(submitted_by.id) if submitted_by else "anonymous",
        metadata={
            "company_id": str(company.id),
            "request_type": dsr.request_type,
            "subject_email": dsr.subject_email,
        },
    )
    return dsr


@transaction.atomic
def verify_dsr_identity(
    request: DSRRequest,
    *,
    actor_id: str,
    notes: str = "",
) -> DSRRequest:
    """Mark a :class:`DSRRequest` as identity-verified.

    Only requests in :attr:`DSRRequestStatus.PENDING` can be verified.
    """
    return _transition_dsr(
        request,
        target=str(DSRRequestStatus.VERIFIED),
        actor_id=actor_id,
        notes=notes,
    )


@transaction.atomic
def start_dsr_work(
    request: DSRRequest,
    *,
    actor_id: str,
    notes: str = "",
) -> DSRRequest:
    """Move a verified :class:`DSRRequest` into :attr:`IN_PROGRESS`."""
    return _transition_dsr(
        request,
        target=str(DSRRequestStatus.IN_PROGRESS),
        actor_id=actor_id,
        notes=notes,
    )


@transaction.atomic
def complete_dsr_request(
    request: DSRRequest,
    *,
    actor_id: str,
    decided_by: User,
    notes: str = "",
) -> DSRRequest:
    """Mark a :class:`DSRRequest` as :attr:`COMPLETED` with a decision user."""
    if request.status not in _ALLOWED_DSR_TRANSITIONS:
        raise DSRError(f"Cannot complete a request in {request.status} state.")
    if DSRRequestStatus.COMPLETED not in _ALLOWED_DSR_TRANSITIONS[request.status]:
        raise DSRError(f"Cannot complete a request in {request.status} state.")
    request.decided_by = decided_by
    return _transition_dsr(
        request,
        target=str(DSRRequestStatus.COMPLETED),
        actor_id=actor_id,
        notes=notes,
        update={"decided_at": timezone.now()},
    )


@transaction.atomic
def reject_dsr_request(
    request: DSRRequest,
    *,
    actor_id: str,
    decided_by: User,
    reason: str,
) -> DSRRequest:
    """Reject a :class:`DSRRequest` with a written reason."""
    if not reason.strip():
        raise DSRError("A rejection reason is required.")
    request.decided_by = decided_by
    return _transition_dsr(
        request,
        target=str(DSRRequestStatus.REJECTED),
        actor_id=actor_id,
        notes=reason,
        update={"decided_at": timezone.now(), "decision_notes": reason},
    )


def _transition_dsr(
    request: DSRRequest,
    *,
    target: str,
    actor_id: str,
    notes: str = "",
    update: dict | None = None,
) -> DSRRequest:
    """Move a :class:`DSRRequest` to ``target`` and emit an audit event.

    Args:
        request: The :class:`DSRRequest` to transition.
        target: The new :class:`DSRRequestStatus`.
        actor_id: Audit actor id.
        notes: Optional notes; stored on the request when provided.
        update: Optional additional field updates.

    Returns:
        The transitioned request.

    Raises:
        DSRError: If the transition is not allowed.
    """
    previous_status = request.status
    allowed = _ALLOWED_DSR_TRANSITIONS.get(previous_status, set())
    if target not in allowed:
        raise DSRError(f"Cannot transition DSR request from {request.status} to {target}.")
    update_fields = ["status", "updated_at"]
    request.status = target
    if notes:
        request.decision_notes = notes
        update_fields.append("decision_notes")
    if getattr(request, "decided_by_id", None) is not None and "decided_by" not in update_fields:
        update_fields.append("decided_by")
    if update:
        for field_name, value in update.items():
            setattr(request, field_name, value)
            if field_name not in update_fields:
                update_fields.append(field_name)
    request.save(update_fields=update_fields)
    record_audit_event(
        event_type="compliance.dsr.decided",
        target_type="dsr_request",
        target_id=str(request.id),
        actor_id=actor_id,
        before={"status": previous_status},
        after={"status": target, "notes": notes},
    )
    return request


# ---------------------------------------------------------------------------
# Legal document registry
# ---------------------------------------------------------------------------


@transaction.atomic
def publish_legal_document(
    *,
    kind: str,
    version: str,
    content_path: str,
    summary: str,
    effective_date: date,
    published_by: User,
    supersedes_version: str = "",
) -> LegalDocument:
    """Publish a new version of a :class:`LegalDocument`.

    The new version becomes the current published version for the
    document kind; any previous current version is unflagged. The
    supersession link is recorded through ``supersedes_version``.

    Args:
        kind: One of :class:`LegalDocumentKind` values.
        version: Semver-style version string (e.g. ``v1.0``).
        content_path: Repository-relative path to the document body.
        summary: Short human-readable abstract.
        effective_date: Date the version takes effect.
        published_by: The :class:`User` publishing the version.
        supersedes_version: The version being replaced, if any.

    Returns:
        The newly created :class:`LegalDocument`.
    """
    if kind not in LegalDocumentKind.values:
        raise DocumentVersionError(f"Unknown document kind: {kind!r}")
    if not version.strip():
        raise DocumentVersionError("version is required.")
    if isinstance(effective_date, str):
        effective_date = date.fromisoformat(effective_date)
    if LegalDocument.objects.filter(kind=kind, version=version).exists():
        raise DocumentVersionError(f"{kind}@{version} is already published.")

    previous_current = LegalDocument.objects.filter(kind=kind, is_current=True).first()
    LegalDocument.objects.filter(kind=kind, is_current=True).update(is_current=False)

    document = LegalDocument.objects.create(
        kind=kind,
        version=version,
        content_path=content_path,
        summary=summary,
        effective_date=effective_date,
        supersedes_version=supersedes_version or (previous_current.version if previous_current else ""),
        published_by=published_by,
        is_current=True,
    )
    record_audit_event(
        event_type="compliance.legal_document.published",
        target_type="legal_document",
        target_id=str(document.id),
        actor_id=str(published_by.id),
        before={"is_current": False, "previous_version": document.supersedes_version},
        after={
            "kind": document.kind,
            "version": document.version,
            "effective_date": document.effective_date.isoformat(),
            "is_current": True,
        },
    )
    return document


def current_legal_document(kind: str) -> LegalDocument | None:
    """Return the currently published :class:`LegalDocument` for a kind."""
    return LegalDocument.objects.filter(kind=kind, is_current=True).order_by("-effective_date").first()


def legal_document_path(document: LegalDocument) -> Path:
    """Resolve the on-disk path for a :class:`LegalDocument`.

    Args:
        document: The :class:`LegalDocument` to resolve.

    Returns:
        Absolute :class:`Path` to the published file under the
        repository root.
    """
    return (REPO_ROOT / document.content_path).resolve()
