from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.identity.models import User
from apps.platform_core.service_base import audited_service
from apps.tenancy.models import Company

from .models import ConnectorHealthStatus, ConnectorStatus, TenantConnectorEnrollment


@audited_service(event_type="CONNECTOR_ENROLLED", target_type="tenant_connector_enrollment")
def enroll_connector(
    company: Company,
    user: User,
    connector_version: str,
    shared_secret_fingerprint: str,
    health_ttl_seconds: int = 300,
) -> TenantConnectorEnrollment:
    enrollment, _created = TenantConnectorEnrollment.objects.get_or_create(
        company=company,
        defaults={
            "connector_version": connector_version,
            "compatibility_window": ">=0.1,<1.0",
            "status": ConnectorStatus.ACTIVE,
            "health_status": ConnectorHealthStatus.OFFLINE,
            "shared_secret_fingerprint": shared_secret_fingerprint,
            "health_ttl_seconds": health_ttl_seconds,
            "created_by": user,
        },
    )
    enrollment.connector_version = connector_version
    enrollment.status = ConnectorStatus.ACTIVE
    enrollment.health_status = ConnectorHealthStatus.OFFLINE
    enrollment.shared_secret_fingerprint = shared_secret_fingerprint.lower()
    enrollment.last_seen_at = None
    enrollment.health_expires_at = None
    enrollment.health_ttl_seconds = health_ttl_seconds
    enrollment.save()
    return enrollment


@transaction.atomic
def observe_connector_health(
    enrollment_id: str,
    connector_version: str,
    shared_secret: str,
    provider_status: str,
) -> TenantConnectorEnrollment:
    enrollment = TenantConnectorEnrollment.objects.select_for_update().filter(id=enrollment_id).first()
    fingerprint = hashlib.sha256(shared_secret.encode("utf-8")).hexdigest()
    if (
        enrollment is None
        or enrollment.status != ConnectorStatus.ACTIVE
        or not hmac.compare_digest(enrollment.shared_secret_fingerprint, fingerprint)
        or enrollment.connector_version != connector_version
    ):
        raise PermissionError("Invalid connector credentials.")

    observed_at = timezone.now()
    enrollment.last_seen_at = observed_at
    enrollment.health_status = provider_status
    enrollment.health_expires_at = (
        observed_at + timedelta(seconds=enrollment.health_ttl_seconds)
        if provider_status != ConnectorHealthStatus.OFFLINE
        else observed_at
    )
    enrollment.save(update_fields=["last_seen_at", "health_status", "health_expires_at", "updated_at"])
    record_audit_event(
        event_type="CONNECTOR_HEALTH_OBSERVED",
        target_type="tenant_connector_enrollment",
        target_id=str(enrollment.id),
        branch_id="",
        metadata={"connector_version": connector_version, "provider_status": provider_status},
    )
    return enrollment


@transaction.atomic
def current_connector_health(enrollment: TenantConnectorEnrollment) -> TenantConnectorEnrollment:
    enrollment = TenantConnectorEnrollment.objects.select_for_update().get(id=enrollment.id)
    expired = enrollment.health_expires_at is None or enrollment.health_expires_at <= timezone.now()
    if enrollment.status != ConnectorStatus.ACTIVE or expired:
        if enrollment.health_status != ConnectorHealthStatus.OFFLINE:
            before = {"health_status": enrollment.health_status}
            enrollment.health_status = ConnectorHealthStatus.OFFLINE
            enrollment.save(update_fields=["health_status", "updated_at"])
            record_audit_event(
                event_type="CONNECTOR_HEALTH_OFFLINE",
                target_type="tenant_connector_enrollment",
                target_id=str(enrollment.id),
                branch_id="",
                before=before,
                after={"health_status": enrollment.health_status},
                metadata={"reason": "heartbeat_expired" if expired else "connector_inactive"},
            )
    return enrollment


@transaction.atomic
def revoke_connector(company: Company, user: User, reason: str = "") -> TenantConnectorEnrollment:
    enrollment = TenantConnectorEnrollment.objects.select_for_update().get(company=company)
    enrollment.status = ConnectorStatus.REVOKED
    enrollment.health_status = ConnectorHealthStatus.OFFLINE
    enrollment.revoked_at = timezone.now()
    enrollment.save(update_fields=["status", "health_status", "revoked_at", "updated_at"])
    record_audit_event(
        event_type="CONNECTOR_REVOKED",
        target_type="tenant_connector_enrollment",
        target_id=str(enrollment.id),
        actor_id=str(user.id),
        branch_id="",
        metadata={"reason": reason},
    )
    return enrollment
