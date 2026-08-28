"""API tests for the compliance module."""

from __future__ import annotations

import pytest
from django.test import Client

from apps.compliance.models import (
    DSRRequest,
    DSRRequestType,
    LegalBasis,
    LegalDocumentKind,
)
from apps.compliance.services import (
    publish_legal_document,
    publish_processing_activity,
)
from apps.organizations.models import CompanyMembership, CompanyRole

pytestmark = pytest.mark.django_db


def test_ropa_endpoint_lists_published_activities():
    client = Client()
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
    response = client.get("/api/v1/compliance/ropa")
    assert response.status_code == 200
    payload = response.json()
    assert "activities" in payload
    assert any(item["name"] == "evidence_capture" for item in payload["activities"])


def test_dsr_intake_creates_request(force_login_company, make_user, make_company):
    user = make_user()
    company = make_company(owner=user)
    CompanyMembership.objects.create(company=company, user=user, role=CompanyRole.OWNER)
    client = force_login_company(user, company)
    response = client.post(
        "/api/v1/compliance/dsr",
        data={
            "request_type": DSRRequestType.ACCESS,
            "subject_email": "subject@example.com",
            "description": "Please send my data.",
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    payload = response.json()
    assert payload["request_type"] == DSRRequestType.ACCESS
    assert payload["status"] == "pending"
    assert DSRRequest.objects.filter(company=company, subject_email="subject@example.com").count() == 1


def test_legal_documents_endpoint_lists_current_documents(make_user):
    publisher = make_user()
    publish_legal_document(
        kind=LegalDocumentKind.TERMS,
        version="v1.0",
        content_path="docs/legal/01_TERMS_OF_USE/v1.0.md",
        summary="Terms of Use v1.0",
        effective_date="2026-01-01",
        published_by=publisher,
    )
    response = Client().get("/api/v1/compliance/legal-documents")
    assert response.status_code == 200
    payload = response.json()
    assert any(item["kind"] == "terms" and item["version"] == "v1.0" for item in payload["documents"])

