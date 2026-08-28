from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.connector_control.models import ConnectorHealthStatus
from apps.connector_control.services import enroll_connector


pytestmark = pytest.mark.django_db


def _fingerprint(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def test_connector_enrollment_and_health(make_user, make_company, make_membership, force_login_company):
    owner = make_user(login_id="connector-owner", display_name="Owner")
    company = make_company(name="Connector Co", code="connector-co", owner=owner)
    make_membership(user=owner, company=company)
    client = force_login_company(owner, company)

    secret = "connector-secret"
    enroll = client.post(
        "/api/v1/connectors/enrollment",
        data={"connector_version": "1.0.0", "shared_secret_fingerprint": _fingerprint(secret)},
        content_type="application/json",
    )
    assert enroll.status_code == 201

    health = client.get("/api/v1/connectors/health")
    assert health.status_code == 200
    assert health.json()["status"] == "offline"

    heartbeat = client.post(
        "/api/v1/connectors/heartbeat",
        data={
            "enrollment_id": enroll.json()["id"],
            "connector_version": "1.0.0",
            "provider_status": "healthy",
        },
        content_type="application/json",
        HTTP_X_CONNECTOR_SECRET=secret,
    )
    assert heartbeat.status_code == 200
    assert heartbeat.json()["health_status"] == "healthy"
    assert heartbeat.json()["last_seen_at"] is not None
    assert heartbeat.json()["health_expires_at"] is not None


def test_connector_stale_and_explicit_offline_health_are_observed(make_user, make_company, make_membership, force_login_company):
    owner = make_user(login_id="connector-owner-stale", display_name="Owner")
    company = make_company(name="Connector Stale Co", code="connector-stale-co", owner=owner)
    make_membership(user=owner, company=company)
    enrollment = enroll_connector(company, owner, "1.0.0", _fingerprint("stale-secret"), 30)

    client = Client()
    observed = client.post(
        "/api/v1/connectors/heartbeat",
        data={"enrollment_id": str(enrollment.id), "connector_version": "1.0.0", "provider_status": "healthy"},
        content_type="application/json",
        HTTP_X_CONNECTOR_SECRET="stale-secret",
    )
    assert observed.status_code == 200

    enrollment.health_expires_at = timezone.now() - timedelta(seconds=1)
    enrollment.save(update_fields=["health_expires_at"])
    client = force_login_company(owner, company)
    stale = client.get("/api/v1/connectors/health")
    assert stale.status_code == 200
    assert stale.json()["status"] == ConnectorHealthStatus.OFFLINE
    assert AuditEvent.objects.filter(event_type="CONNECTOR_HEALTH_OFFLINE", target_id=str(enrollment.id)).exists()

    offline = client.post(
        "/api/v1/connectors/heartbeat",
        data={"enrollment_id": str(enrollment.id), "connector_version": "1.0.0", "provider_status": "offline"},
        content_type="application/json",
        HTTP_X_CONNECTOR_SECRET="stale-secret",
    )
    assert offline.status_code == 200
    assert offline.json()["health_status"] == ConnectorHealthStatus.OFFLINE
    assert offline.json()["last_seen_at"] is not None


def test_connector_heartbeat_cannot_cross_tenant_enrollments(make_user, make_company):
    first_owner = make_user(login_id="connector-owner-a", display_name="Owner A")
    second_owner = make_user(login_id="connector-owner-b", display_name="Owner B")
    first_company = make_company(name="Connector A", code="connector-a", owner=first_owner)
    second_company = make_company(name="Connector B", code="connector-b", owner=second_owner)
    first_enrollment = enroll_connector(first_company, first_owner, "1.0.0", _fingerprint("secret-a"))
    second_enrollment = enroll_connector(second_company, second_owner, "1.0.0", _fingerprint("secret-b"))

    response = Client().post(
        "/api/v1/connectors/heartbeat",
        data={"enrollment_id": str(second_enrollment.id), "connector_version": "1.0.0", "provider_status": "healthy"},
        content_type="application/json",
        HTTP_X_CONNECTOR_SECRET="secret-a",
    )
    assert response.status_code == 403
    second_enrollment.refresh_from_db()
    assert second_enrollment.health_status == ConnectorHealthStatus.OFFLINE
    assert second_enrollment.last_seen_at is None
    assert first_enrollment.company_id != second_enrollment.company_id


def test_connector_revoke_sets_offline_status(make_user, make_company, make_membership, force_login_company):
    owner = make_user(login_id="connector-owner-2", display_name="Owner")
    company = make_company(name="Connector Co 2", code="connector-co-2", owner=owner)
    make_membership(user=owner, company=company)
    client = force_login_company(owner, company)

    enroll = client.post(
        "/api/v1/connectors/enrollment",
        data={"connector_version": "1.0.0", "shared_secret_fingerprint": _fingerprint("revoke-secret")},
        content_type="application/json",
    )
    assert enroll.status_code == 201

    revoked = client.post("/api/v1/connectors/revoke", data={"reason": "outage"}, content_type="application/json")
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["health_status"] == "offline"

    health = client.get("/api/v1/connectors/health")
    assert health.status_code == 200
    assert health.json()["status"] == "offline"
