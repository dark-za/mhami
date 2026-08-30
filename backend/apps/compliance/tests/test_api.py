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


def test_dsr_list_get_forbidden_for_employee(force_login_company, make_user, make_company):
    owner = make_user()
    company = make_company(owner=owner)
    CompanyMembership.objects.create(company=company, user=owner, role=CompanyRole.OWNER)
    employee = make_user()
    CompanyMembership.objects.create(company=company, user=employee, role=CompanyRole.EMPLOYEE)
    DSRRequest.objects.create(
        company=company,
        request_type=DSRRequestType.ACCESS,
        subject_email="subject@example.com",
        description="test",
    )
    client = force_login_company(employee, company)
    response = client.get("/api/v1/compliance/dsr")
    assert response.status_code == 403


def test_dsr_list_get_allowed_for_owner(force_login_company, make_user, make_company):
    owner = make_user()
    company = make_company(owner=owner)
    CompanyMembership.objects.create(company=company, user=owner, role=CompanyRole.OWNER)
    other_owner = make_user()
    other_company = make_company(owner=other_owner)
    CompanyMembership.objects.create(
        company=other_company, user=other_owner, role=CompanyRole.OWNER
    )
    DSRRequest.objects.create(
        company=company,
        request_type=DSRRequestType.ACCESS,
        subject_email="owner-subject@example.com",
        description="owner request",
    )
    DSRRequest.objects.create(
        company=other_company,
        request_type=DSRRequestType.ACCESS,
        subject_email="other@example.com",
        description="other",
    )
    client = force_login_company(owner, company)
    response = client.get("/api/v1/compliance/dsr")
    assert response.status_code == 200
    payload = response.json()
    assert "requests" in payload
    assert len(payload["requests"]) == 1
    assert payload["requests"][0]["subject_email"] == "owner-subject@example.com"


def test_dsr_list_get_allowed_for_monitor(force_login_company, make_user, make_company):
    owner = make_user()
    company = make_company(owner=owner)
    CompanyMembership.objects.create(company=company, user=owner, role=CompanyRole.OWNER)
    monitor = make_user()
    CompanyMembership.objects.create(company=company, user=monitor, role=CompanyRole.MONITOR)
    DSRRequest.objects.create(
        company=company,
        request_type=DSRRequestType.ERASURE,
        subject_email="monitor-subject@example.com",
        description="monitor request",
    )
    client = force_login_company(monitor, company)
    response = client.get("/api/v1/compliance/dsr")
    assert response.status_code == 200
    payload = response.json()
    assert "requests" in payload
    assert any(r["subject_email"] == "monitor-subject@example.com" for r in payload["requests"])


def test_dsr_post_allowed_for_employee(force_login_company, make_user, make_company):
    owner = make_user()
    company = make_company(owner=owner)
    CompanyMembership.objects.create(company=company, user=owner, role=CompanyRole.OWNER)
    employee = make_user()
    CompanyMembership.objects.create(company=company, user=employee, role=CompanyRole.EMPLOYEE)
    client = force_login_company(employee, company)
    response = client.post(
        "/api/v1/compliance/dsr",
        data={
            "request_type": DSRRequestType.ACCESS,
            "subject_email": "employee-subject@example.com",
            "description": "Employee submits request.",
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    assert DSRRequest.objects.filter(
        company=company, subject_email="employee-subject@example.com"
    ).exists()

