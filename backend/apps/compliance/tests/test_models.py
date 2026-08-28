"""Unit tests for the compliance models."""

from __future__ import annotations

import pytest

from apps.compliance.models import (
    DSRRequest,
    DSRRequestStatus,
    DSRRequestType,
    LegalBasis,
    LegalDocument,
    LegalDocumentKind,
)
from apps.compliance.services import current_legal_document, publish_legal_document

pytestmark = pytest.mark.django_db


def test_processing_activity_choices_are_stable():
    """The ROPA lawful-basis choices mirror the documented legal bases."""
    assert LegalBasis.CONTRACT in LegalBasis.values
    assert LegalBasis.CONSENT in LegalBasis.values
    assert LegalBasis.LEGITIMATE_INTERESTS in LegalBasis.values
    assert LegalBasis.LEGAL_OBLIGATION in LegalBasis.values


def test_dsr_request_initial_status_is_pending(make_user, make_company):
    """A newly submitted DSR request starts in PENDING until identity is verified."""
    company = make_company()
    submitter = make_user()
    request = DSRRequest.objects.create(
        company=company,
        submitted_by=submitter,
        request_type=DSRRequestType.ACCESS,
        subject_email="subject@example.com",
    )
    assert request.status == DSRRequestStatus.PENDING
    assert request.decided_at is None
    assert request.decided_by is None


def test_legal_document_is_current_after_publication(make_user):
    """Publishing a legal document makes it the current one for its kind."""
    publisher = make_user()
    publish_legal_document(
        kind=LegalDocumentKind.TERMS,
        version="v1.0",
        content_path="docs/legal/01_TERMS_OF_USE/v1.0.md",
        summary="Terms of Use v1.0",
        effective_date="2026-01-01",
        published_by=publisher,
    )
    current = current_legal_document(LegalDocumentKind.TERMS)
    assert current is not None
    assert current.version == "v1.0"
    assert current.is_current is True


def test_legal_document_supersedes_previous_version(make_user):
    """Publishing a new version unflags the previous current version."""
    publisher = make_user()
    publish_legal_document(
        kind=LegalDocumentKind.PRIVACY,
        version="v1.0",
        content_path="docs/legal/02_PRIVACY_NOTICE/v1.0.md",
        summary="Privacy Notice v1.0",
        effective_date="2026-01-01",
        published_by=publisher,
    )
    publish_legal_document(
        kind=LegalDocumentKind.PRIVACY,
        version="v1.1",
        content_path="docs/legal/02_PRIVACY_NOTICE/v1.1.md",
        summary="Privacy Notice v1.1",
        effective_date="2026-06-01",
        published_by=publisher,
    )
    rows = list(LegalDocument.objects.filter(kind=LegalDocumentKind.PRIVACY).order_by("version"))
    assert [row.version for row in rows] == ["v1.0", "v1.1"]
    assert [row.is_current for row in rows] == [False, True]
