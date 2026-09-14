from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone

from apps.agent_access.models import AgentGrant
from apps.organizations.models import CompanyRole
from apps.tasks.models import TaskAssignmentMode, TaskInstance


MCP_GRANT_SECRET = "test-mcp-grant-secret"


def _body(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _signed_headers(
    grant: AgentGrant,
    body: bytes,
    *,
    nonce: str = "nonce-1",
    grant_secret: str = MCP_GRANT_SECRET,
    fingerprint: str | None = None,
) -> dict[str, str]:
    timestamp = datetime.now(UTC).isoformat()
    request_id = str(uuid4())
    client_fingerprint = fingerprint or grant.client_fingerprint
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = "\n".join(
        [timestamp, nonce, str(grant.id), request_id, client_fingerprint, body_hash]
    ).encode("utf-8")
    signature = hmac.new(grant_secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return {
        "HTTP_X_MHAMI_TIMESTAMP": timestamp,
        "HTTP_X_MHAMI_NONCE": nonce,
        "HTTP_X_AGENT_GRANT_ID": str(grant.id),
        "HTTP_X_REQUEST_ID": request_id,
        "HTTP_X_MHAMI_CLIENT_FINGERPRINT": client_fingerprint,
        "HTTP_X_MHAMI_GRANT_SECRET": grant_secret,
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
        client_fingerprint="sha256:" + ("1" * 64),
        secret_hash=make_password(MCP_GRANT_SECRET),
        scopes=["read:tasks", "read:reports", "write:tasks:transfer"],
        expires_at=timezone.now() + timedelta(days=1),
    )


@pytest.mark.django_db
def test_mcp_initialize_requires_valid_per_grant_secret(client, mcp_grant: AgentGrant) -> None:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    body = _body(payload)
    accepted = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body),
    )
    rejected = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="bad", grant_secret="wrong-secret"),
    )

    assert accepted.status_code == 200
    assert accepted.json()["result"]["protocolVersion"] == "2026-07-28"
    assert rejected.status_code in {401, 403}

    # A rejected request must not consume a nonce that the genuine client can use.
    valid_retry = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="bad"),
    )
    assert valid_retry.status_code == 200


@pytest.mark.django_db
def test_mcp_rejects_nonce_replay_and_fingerprint_mismatch(client, mcp_grant: AgentGrant) -> None:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    body = _body(payload)
    headers = _signed_headers(mcp_grant, body)
    assert (
        client.post(
            "/api/v1/agent/mcp", data=body, content_type="application/json", **headers
        ).status_code
        == 200
    )
    assert client.post(
        "/api/v1/agent/mcp", data=body, content_type="application/json", **headers
    ).status_code in {401, 403}
    mismatch = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="fingerprint", fingerprint="sha256:" + ("2" * 64)),
    )
    assert mismatch.status_code in {401, 403}


@pytest.mark.django_db
def test_mcp_rejects_inactive_grant_user(client, mcp_grant: AgentGrant) -> None:
    mcp_grant.user.company_memberships.filter(company=mcp_grant.company).update(active=False)
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    body = _body(payload)
    response = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body),
    )
    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_mcp_rejects_cross_grant_impersonation(
    client, mcp_grant: AgentGrant, make_company, make_membership, make_user
) -> None:
    other_user = make_user()
    other_company = make_company(owner=other_user)
    make_membership(user=other_user, company=other_company, role=CompanyRole.OWNER)
    other_grant = AgentGrant.objects.create(
        company=other_company,
        user=other_user,
        client_name="Other MCP",
        client_fingerprint="sha256:" + ("3" * 64),
        secret_hash=make_password("other-grant-secret"),
        scopes=["read:tasks"],
        expires_at=timezone.now() + timedelta(days=1),
    )
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    body = _body(payload)
    response = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(other_grant, body, grant_secret=MCP_GRANT_SECRET),
    )
    assert response.status_code in {401, 403}


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
    assert {tool["name"] for tool in response.json()["result"]["tools"]} == {"tasks.list"}


@pytest.mark.django_db
def test_mcp_employee_only_reads_own_tasks(
    client,
    make_branch,
    make_company,
    make_membership,
    make_template,
    make_template_version,
    make_user,
) -> None:
    employee, other_employee = make_user(), make_user()
    company = make_company(owner=make_user())
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    make_membership(user=other_employee, company=company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=company)
    grant = AgentGrant.objects.create(
        company=company,
        user=employee,
        client_name="Employee MCP",
        client_fingerprint="sha256:" + ("4" * 64),
        secret_hash=make_password(MCP_GRANT_SECRET),
        scopes=["read:tasks"],
        expires_at=timezone.now() + timedelta(days=1),
    )
    template = make_template(
        company=company,
        branch=branch,
        assignment_mode=TaskAssignmentMode.NAMED_USER,
        assigned_user=other_employee,
    )
    version = make_template_version(template=template)
    TaskInstance.objects.create(
        company=company,
        branch=branch,
        template=template,
        template_version=version,
        scheduled_for=timezone.now(),
        due_at=timezone.now() + timedelta(hours=1),
        assigned_user=other_employee,
    )
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "tasks.list", "idempotency_key": "employee-read", "arguments": {}},
    }
    body = _body(payload)
    response = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(grant, body),
    )
    assert response.status_code == 200
    assert response.json()["result"]["result"]["tasks"] == []


@pytest.mark.django_db
def test_mcp_transfer_replays_the_same_idempotency_key(
    client,
    make_branch,
    make_branch_membership,
    make_membership,
    make_template,
    make_template_version,
    make_user,
    mcp_grant: AgentGrant,
) -> None:
    target = make_user()
    make_membership(user=target, company=mcp_grant.company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=mcp_grant.company)
    make_branch_membership(user=target, company=mcp_grant.company, branch=branch)
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
        "id": "transfer",
        "method": "tools/call",
        "params": {
            "name": "tasks.transfer.request",
            "idempotency_key": "transfer-1",
            "arguments": {
                "task_id": str(instance.id),
                "requested_to_id": str(target.id),
                "reason": "handoff",
            },
        },
    }
    body = _body(payload)
    first = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body),
    )
    replay = client.post(
        "/api/v1/agent/mcp",
        data=body,
        content_type="application/json",
        **_signed_headers(mcp_grant, body, nonce="transfer-replay"),
    )
    assert first.status_code == 200
    assert first.json()["result"]["replayed"] is False
    assert replay.status_code == 200
    assert replay.json()["result"]["replayed"] is True


@pytest.mark.django_db
def test_mcp_transfer_rejects_an_expired_target_branch_membership(
    client,
    make_branch,
    make_branch_membership,
    make_membership,
    make_template,
    make_template_version,
    make_user,
    mcp_grant: AgentGrant,
) -> None:
    target = make_user()
    make_membership(user=target, company=mcp_grant.company, role=CompanyRole.EMPLOYEE)
    branch = make_branch(company=mcp_grant.company)
    make_branch_membership(
        user=target,
        company=mcp_grant.company,
        branch=branch,
        active=True,
        active_until=timezone.now() - timedelta(minutes=1),
    )
    template = make_template(
        company=mcp_grant.company,
        branch=branch,
        assignment_mode=TaskAssignmentMode.NAMED_USER,
        assigned_user=mcp_grant.user,
    )
    instance = TaskInstance.objects.create(
        company=mcp_grant.company,
        branch=branch,
        template=template,
        template_version=make_template_version(template=template),
        scheduled_for=timezone.now(),
        due_at=timezone.now() + timedelta(hours=1),
        assigned_user=mcp_grant.user,
    )
    payload = {
        "jsonrpc": "2.0",
        "id": "expired-target",
        "method": "tools/call",
        "params": {
            "name": "tasks.transfer.request",
            "idempotency_key": "expired-target-membership",
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
        **_signed_headers(mcp_grant, body),
    )
    assert response.status_code == 403
