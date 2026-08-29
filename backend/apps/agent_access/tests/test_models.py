from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.agent_access.models import (
    AgentActionLog,
    AgentGrant,
    AgentGrantStatus,
    AgentScope,
    arguments_hash,
)
from apps.agent_access.services import create_agent_grant, record_agent_action
from apps.organizations.models import CompanyRole


@pytest.fixture
def agent_grant(make_company, make_user) -> AgentGrant:
    user = make_user()
    company = make_company(owner=user)
    return AgentGrant.objects.create(
        company=company,
        user=user,
        client_name="Mhami MCP",
        client_fingerprint="sha256:test-client",
        scopes=[AgentScope.READ_TASKS, AgentScope.WRITE_TASKS_TRANSFER],
        expires_at=timezone.now() + timedelta(days=1),
    )


@pytest.mark.django_db
def test_agent_grant_validates_known_scopes(agent_grant: AgentGrant) -> None:
    agent_grant.full_clean()

    agent_grant.scopes = ["write:anything"]
    with pytest.raises(ValidationError):
        agent_grant.full_clean()


@pytest.mark.django_db
def test_agent_grant_active_requires_current_unrevoked_grant(agent_grant: AgentGrant) -> None:
    assert agent_grant.active is True

    agent_grant.revoked_at = timezone.now()
    assert agent_grant.active is False

    agent_grant.revoked_at = None
    agent_grant.status = AgentGrantStatus.REVOKED
    assert agent_grant.active is False

    agent_grant.status = AgentGrantStatus.ACTIVE
    agent_grant.expires_at = timezone.now() - timedelta(seconds=1)
    assert agent_grant.active is False


def test_arguments_hash_is_canonical_and_input_sensitive() -> None:
    first = arguments_hash({"task_id": "1", "to_user_id": "2"})
    reordered = arguments_hash({"to_user_id": "2", "task_id": "1"})
    changed = arguments_hash({"task_id": "1", "to_user_id": "3"})

    assert first == reordered
    assert first != changed


@pytest.mark.django_db
def test_agent_action_log_enforces_idempotency_per_grant_tool(agent_grant: AgentGrant) -> None:
    payload_hash = arguments_hash({"task_id": "1"})
    AgentActionLog.objects.create(
        grant=agent_grant,
        company=agent_grant.company,
        request_id=uuid4(),
        tool_name="tasks.transfer",
        required_scope=AgentScope.WRITE_TASKS_TRANSFER,
        idempotency_key="idem-1",
        arguments_hash=payload_hash,
    )

    with pytest.raises(IntegrityError):
        AgentActionLog.objects.create(
            grant=agent_grant,
            company=agent_grant.company,
            request_id=uuid4(),
            tool_name="tasks.transfer",
            required_scope=AgentScope.WRITE_TASKS_TRANSFER,
            idempotency_key="idem-1",
            arguments_hash=payload_hash,
        )


@pytest.mark.django_db
def test_record_agent_action_reuses_matching_idempotency_key(agent_grant: AgentGrant) -> None:
    first, created = record_agent_action(
        grant=agent_grant,
        tool_name="tasks.transfer",
        required_scope=AgentScope.WRITE_TASKS_TRANSFER,
        idempotency_key="idem-2",
        arguments={"task_id": "1", "to_user_id": "2"},
    )
    second, reused = record_agent_action(
        grant=agent_grant,
        tool_name="tasks.transfer",
        required_scope=AgentScope.WRITE_TASKS_TRANSFER,
        idempotency_key="idem-2",
        arguments={"to_user_id": "2", "task_id": "1"},
    )

    assert created is True
    assert reused is False
    assert second.id == first.id


@pytest.mark.django_db
def test_record_agent_action_rejects_idempotency_key_with_different_arguments(
    agent_grant: AgentGrant,
) -> None:
    record_agent_action(
        grant=agent_grant,
        tool_name="tasks.transfer",
        required_scope=AgentScope.WRITE_TASKS_TRANSFER,
        idempotency_key="idem-3",
        arguments={"task_id": "1", "to_user_id": "2"},
    )

    with pytest.raises(ValidationError):
        record_agent_action(
            grant=agent_grant,
            tool_name="tasks.transfer",
            required_scope=AgentScope.WRITE_TASKS_TRANSFER,
            idempotency_key="idem-3",
            arguments={"task_id": "1", "to_user_id": "3"},
        )


@pytest.mark.django_db
def test_create_agent_grant_requires_company_owner(make_company, make_membership, make_user) -> None:
    owner = make_user()
    employee = make_user()
    company = make_company(owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)

    grant = create_agent_grant(
        owner_id=owner.id,
        company=company,
        user_id=owner.id,
        client_name="Mhami MCP",
        client_fingerprint="sha256:test-client",
        scopes=["read:tasks"],
        expires_at=timezone.now() + timedelta(days=1),
    )

    assert grant.company == company
    with pytest.raises(PermissionDenied):
        create_agent_grant(
            owner_id=employee.id,
            company=company,
            user_id=employee.id,
            client_name="Mhami MCP",
            client_fingerprint="sha256:test-client-2",
            scopes=["read:tasks"],
            expires_at=timezone.now() + timedelta(days=1),
        )
