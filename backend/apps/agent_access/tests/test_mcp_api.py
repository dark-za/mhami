from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone

from apps.agent_access.models import AgentGrant
from apps.organizations.models import CompanyRole
from apps.tasks.models import TaskAssignmentMode, TaskInstance


MCP_SECRET = "test-mcp-secret"


def _body(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _signed_headers(grant: AgentGrant, body: bytes, *, nonce: str = "nonce-1") -> dict[str, str]:
    timestamp = datetime.now(UTC).isoformat()
    request_id = str(uuid4())
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = "\n".join([timestamp, nonce, str(grant.id), request_id, body_hash]).encode("utf-8")
    signature = hmac.new(MCP_SECRET.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return {
        "HTTP_X_MHAMI_TIMESTAMP": timestamp,
        "HTTP_X_MHAMI_NONCE": nonce,
        "HTTP_X_AGENT_GRANT_ID": str(grant.id),
        "HTTP_X_REQUEST_ID": request_id,
        "HTTP_X_MHAMI_SIGNATURE": f"sha256={signature}",
    }


@pytest.fixture(autouse=True)
def clear_mcp_nonce_cache() -> None:
    cache.clear()


@pytest.fixture
def mcp_grant(make_company, make_membership, make_user) -> AgentGrant:
    owner = make_user()
    company = make_company(owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    return AgentGrant.objects.create(
        company=company,
        user=owner,
        client_name="Mhami MCP",
        client_fingerprint="sha256:test-client",
        scopes=["read:tasks", "read:reports", "write:tasks:transfer"],
        expires_at=timezone.now() + timedelta(days=1),
    )


@override_settings(MCP_INTERNAL_HMAC_SECRET=MCP_SECRET)
@pytest.mark.django_db
def test_mcp_initialize_requires_valid_hmac(client, mcp_grant: AgentGrant) -> None:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    body = _body(payload)

    response = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body),
    )

    assert response.status_code == 200
    assert response.json()["result"]["protocolVersion"] == "2026-07-28"

    bad_headers = _signed_headers(mcp_grant, body, nonce="nonce-2")
    bad_headers["HTTP_X_MHAMI_SIGNATURE"] = "sha256=bad"
    rejected = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **bad_headers,
    )
    assert rejected.status_code in {401, 403}

    accepted_after_bad_signature = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="nonce-2"),
    )
    assert accepted_after_bad_signature.status_code == 200


@override_settings(MCP_INTERNAL_HMAC_SECRET=MCP_SECRET)
@pytest.mark.django_db
def test_mcp_rejects_nonce_replay(client, mcp_grant: AgentGrant) -> None:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    body = _body(payload)
    headers = _signed_headers(mcp_grant, body)

    assert client.post("/api/v1/agent/mcp", data=body, content_type="application/json", **headers).status_code == 200
    replay = client.post("/api/v1/agent/mcp", data=body, content_type="application/json", **headers)

    assert replay.status_code in {401, 403}


@override_settings(MCP_INTERNAL_HMAC_SECRET=MCP_SECRET)
@pytest.mark.django_db
def test_mcp_tool_list_respects_grant_scopes(client, mcp_grant: AgentGrant) -> None:
    mcp_grant.scopes = ["read:tasks"]
    mcp_grant.save(update_fields=["scopes"])
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    body = _body(payload)

    response = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body),
    )

    names = {tool["name"] for tool in response.json()["result"]["tools"]}
    assert names == {"tasks.list"}


@override_settings(MCP_INTERNAL_HMAC_SECRET=MCP_SECRET)
@pytest.mark.django_db
def test_mcp_transfer_tool_executes_and_replays_same_idempotency_key(
    client,
    make_branch,
    make_membership,
    make_template,
    make_template_version,
    make_user,
    mcp_grant: AgentGrant,
) -> None:
    target = make_user()
    make_membership(user=target, company=mcp_grant.company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=mcp_grant.company)
    template = make_template(
        company=mcp_grant.company,
        branch=branch,
        assignment_mode=TaskAssignmentMode.NAMED_USER,
        assigned_user=mcp_grant.user,
    )
    version = make_template_version(template=template)
    instance = TaskInstance.objects.create(
        company=mcp_grant.company,
        branch=branch,
        template=template,
        template_version=version,
        scheduled_for=timezone.now(),
        due_at=timezone.now() + timedelta(hours=1),
        assigned_user=mcp_grant.user,
    )
    payload = {
        "jsonrpc": "2.0",
        "id": "call-1",
        "method": "tools/call",
        "params": {
            "name": "tasks.transfer.request",
            "idempotency_key": "idem-transfer-1",
            "arguments": {
                "task_id": str(instance.id),
                "requested_to_id": str(target.id),
                "reason": "handoff",
            },
        },
    }
    body = _body(payload)

    response = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="transfer-1"),
    )
    replay = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="transfer-2"),
    )

    assert response.status_code == 200
    assert response.json()["result"]["replayed"] is False
    assert replay.status_code == 200
    assert replay.json()["result"]["replayed"] is True
    assert replay.json()["result"]["result"] == response.json()["result"]["result"]


@override_settings(MCP_INTERNAL_HMAC_SECRET=MCP_SECRET)
@pytest.mark.django_db
def test_mcp_transfer_rejects_target_outside_grant_company(
    client,
    make_branch,
    make_company,
    make_membership,
    make_template,
    make_template_version,
    make_user,
    mcp_grant: AgentGrant,
) -> None:
    external = make_user()
    external_company = make_company(owner=external)
    make_membership(user=external, company=external_company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=mcp_grant.company)
    template = make_template(
        company=mcp_grant.company,
        branch=branch,
        assignment_mode=TaskAssignmentMode.NAMED_USER,
        assigned_user=mcp_grant.user,
    )
    version = make_template_version(template=template)
    instance = TaskInstance.objects.create(
        company=mcp_grant.company,
        branch=branch,
        template=template,
        template_version=version,
        scheduled_for=timezone.now(),
        due_at=timezone.now() + timedelta(hours=1),
        assigned_user=mcp_grant.user,
    )
    payload = {
        "jsonrpc": "2.0",
        "id": "call-external",
        "method": "tools/call",
        "params": {
            "name": "tasks.transfer.request",
            "idempotency_key": "idem-external-target",
            "arguments": {
                "task_id": str(instance.id),
                "requested_to_id": str(external.id),
                "reason": "external handoff",
            },
        },
    }
    body = _body(payload)

    response = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="transfer-external"),
    )

    assert response.status_code == 403
