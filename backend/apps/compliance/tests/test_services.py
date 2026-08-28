"""Service-layer tests for the compliance module."""

from __future__ import annotations

import pytest

from apps.audit.models import AuditEvent
from apps.compliance.models import (
    DSRRequestStatus,
    DSRRequestType,
    LegalBasis,
    ProcessingActivity,
)
from apps.compliance.services import (
    ComplianceError,
    complete_dsr_request,
    publish_processing_activity,
    reject_dsr_request,
    start_dsr_work,
    submit_dsr_request,
    verify_dsr_identity,
)

pytestmark = pytest.mark.django_db


def test_publish_processing_activity_creates_and_updates(make_user):
    """ROPA rows are upserted by name; the audit chain captures both states."""
    publish_processing_activity(
        name="evidence_capture",
        purpose="Capture evidence.",
        controller="Tenant company",
        data_categories=["camera_images"],
        data_subject_categories=["employees"],
        recipients=["branch monitors"],
        lawful_basis=LegalBasis.LEGITIMATE_INTERESTS,
        retention_days=180,
        security_measures="Private media storage.",
    )
    activity = ProcessingActivity.objects.get(name="evidence_capture")
    assert activity.is_published is True
    assert activity.published_at is not None

    # Re-publish with an updated purpose; the row is updated in place.
    publish_processing_activity(
        name="evidence_capture",
        purpose="Capture evidence with face blur.",
        controller="Tenant company",
        data_categories=["camera_images", "blurred_derivatives"],
        data_subject_categories=["employees"],
        recipients=["branch monitors"],
        lawful_basis=LegalBasis.LEGITIMATE_INTERESTS,
        retention_days=180,
        security_measures="Private media storage + face-blur derivatives.",
    )
    activity.refresh_from_db()
    assert activity.purpose.startswith("Capture evidence with face blur")
    audit_events = list(AuditEvent.objects.filter(event_type="compliance.ropa.published").order_by("id"))
    assert len(audit_events) >= 2


def test_publish_processing_activity_rejects_invalid_basis():
    """A bogus lawful basis is rejected at the service boundary."""
    with pytest.raises(ComplianceError):
        publish_processing_activity(
            name="bogus",
            purpose="Bogus",
            controller="Tenant",
            data_categories=[],
            data_subject_categories=[],
            recipients=[],
            lawful_basis="not-a-real-basis",
            retention_days=10,
            security_measures="n/a",
        )


def test_dsr_lifecycle_round_trip(make_user, make_company):
    """A DSR request can be submitted, verified, started, completed."""
    submitter = make_user()
    decider = make_user()
    company = make_company()
    request = submit_dsr_request(
        company=company,
        request_type=DSRRequestType.ACCESS,
        subject_email="subject@example.com",
        submitted_by=submitter,
    )
    assert request.status == DSRRequestStatus.PENDING
    verify_dsr_identity(request, actor_id=str(submitter.id))
    request.refresh_from_db()
    assert request.status == DSRRequestStatus.VERIFIED
    start_dsr_work(request, actor_id=str(submitter.id))
    request.refresh_from_db()
    assert request.status == DSRRequestStatus.IN_PROGRESS
    complete_dsr_request(request, actor_id=str(decider.id), decided_by=decider)
    request.refresh_from_db()
    assert request.status == DSRRequestStatus.COMPLETED
    assert request.decided_by_id == decider.id
    assert request.decided_at is not None


def test_dsr_rejection_requires_reason(make_user, make_company):
    """A rejection without a reason is rejected by the service."""
    company = make_company()
    decider = make_user()
    request = submit_dsr_request(
        company=company,
        request_type=DSRRequestType.ERASURE,
        subject_email="subject@example.com",
    )
    with pytest.raises(Exception):
        reject_dsr_request(request, actor_id=str(decider.id), decided_by=decider, reason="")
    request.refresh_from_db()
    assert request.status == DSRRequestStatus.PENDING


def test_dsr_invalid_transition_is_rejected(make_user, make_company):
    """A completed DSR request cannot be transitioned again."""
    company = make_company()
    decider = make_user()
    request = submit_dsr_request(
        company=company,
        request_type=DSRRequestType.PORTABILITY,
        subject_email="subject@example.com",
    )
    verify_dsr_identity(request, actor_id=str(decider.id))
    start_dsr_work(request, actor_id=str(decider.id))
    complete_dsr_request(request, actor_id=str(decider.id), decided_by=decider)
    with pytest.raises(Exception):
        start_dsr_work(request, actor_id=str(decider.id))
