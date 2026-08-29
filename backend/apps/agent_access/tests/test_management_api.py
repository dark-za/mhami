from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.agent_access.models import AgentActionLog, AgentGrant
from apps.audit.models import AuditEvent
from apps.organizations.models import CompanyRole


pytestmark = pytest.mark.django_db
CLIENT_FINGERPRINT = "sha256:" + ("a" * 64)
EXTERNAL_FINGERPRINT = "sha256:" + ("b" * 64)


def test_owner_can_create_list_and_revoke_agent_grant(
    force_login_company,
    make_company,
    make_membership,
    make_user,
) -> None:
    owner = make_user()
    company = make_company(owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    client = force_login_company(owner, company)

    created = client.post(
        "/api/v1/agent/grants",
        data={
            "user_id": str(owner.id),
            "client_name": "Owner MCP",
            "client_fingerprint": CLIENT_FINGERPRINT,
            "scopes": ["read:tasks", "write:tasks:transfer"],
            "expires_at": (timezone.now() + timedelta(days=1)).isoformat(),
        },
        content_type="application/json",
    )

    assert created.status_code == 201
    grant_id = created.json()["id"]
    assert created.json()["active"] is True
    assert AuditEvent.objects.filter(event_type="MCP_AGENT_GRANT_CREATED", target_id=grant_id).exists()

    listed = client.get("/api/v1/agent/grants")
    assert listed.status_code == 200
    assert [grant["id"] for grant in listed.json()["grants"]] == [grant_id]

    revoked = client.post(
        f"/api/v1/agent/grants/{grant_id}/revoke",
        data={"reason": "rotation"},
        content_type="application/json",
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["active"] is False
    assert AuditEvent.objects.filter(event_type="MCP_AGENT_GRANT_REVOKED", target_id=grant_id).exists()


def test_employee_cannot_manage_agent_grants(
    force_login_company,
    make_company,
    make_membership,
    make_user,
) -> None:
    owner = make_user()
    employee = make_user()
    company = make_company(owner=owner)
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    client = force_login_company(employee, company)

    response = client.get("/api/v1/agent/grants")

    assert response.status_code == 403


def test_owner_cannot_create_grant_for_external_user(
    force_login_company,
    make_company,
    make_membership,
    make_user,
) -> None:
    owner = make_user()
    external = make_user()
    company = make_company(owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    client = force_login_company(owner, company)

    response = client.post(
        "/api/v1/agent/grants",
        data={
            "user_id": str(external.id),
            "client_name": "External MCP",
            "client_fingerprint": EXTERNAL_FINGERPRINT,
            "scopes": ["read:tasks"],
            "expires_at": (timezone.now() + timedelta(days=1)).isoformat(),
        },
        content_type="application/json",
    )

    assert response.status_code == 403


def test_owner_and_monitor_can_read_agent_logs(
    force_login_company,
    make_company,
    make_membership,
    make_user,
) -> None:
    owner = make_user()
    monitor = make_user()
    company = make_company(owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    grant = AgentGrant.objects.create(
        company=company,
        user=owner,
        client_name="Owner MCP",
        client_fingerprint=CLIENT_FINGERPRINT,
        scopes=["read:tasks"],
        expires_at=timezone.now() + timedelta(days=1),
    )
    log = AgentActionLog.objects.create(
        grant=grant,
        company=company,
        request_id=uuid4(),
        tool_name="tasks.list",
        required_scope="read:tasks",
        idempotency_key="idem-list",
        arguments_hash="a" * 64,
    )

    owner_response = force_login_company(owner, company).get("/api/v1/agent/logs")
    monitor_response = force_login_company(monitor, company).get("/api/v1/agent/logs")

    assert owner_response.status_code == 200
    assert monitor_response.status_code == 200
    assert owner_response.json()["logs"][0]["id"] == str(log.id)
    assert monitor_response.json()["logs"][0]["id"] == str(log.id)


def test_scope_catalog_is_readable_by_management_roles(
    force_login_company,
    make_company,
    make_membership,
    make_user,
) -> None:
    monitor = make_user()
    company = make_company()
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    response = force_login_company(monitor, company).get("/api/v1/agent/scopes")

    assert response.status_code == 200
    assert {"value": "admin:full", "status": "active"} in response.json()["scopes"]


def test_agent_grant_create_rejects_weak_client_fingerprint(
    force_login_company,
    make_company,
    make_membership,
    make_user,
) -> None:
    owner = make_user()
    company = make_company(owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    client = force_login_company(owner, company)

    response = client.post(
        "/api/v1/agent/grants",
        data={
            "user_id": str(owner.id),
            "client_name": "Owner MCP",
            "client_fingerprint": "sha256:not-a-real-digest",
            "scopes": ["read:tasks"],
            "expires_at": (timezone.now() + timedelta(days=1)).isoformat(),
        },
        content_type="application/json",
    )

    assert response.status_code == 400
