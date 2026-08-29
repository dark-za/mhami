from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.agent_access.models import AgentActionLog, AgentGrant, AgentScope, arguments_hash
from apps.audit.services import get_audit_trail, record_audit_event


@pytest.mark.django_db
def test_get_audit_trail_marks_agent_events(make_company, make_user) -> None:
    user = make_user()
    company = make_company(owner=user)
    grant = AgentGrant.objects.create(
        company=company,
        user=user,
        client_name="Mhami MCP",
        client_fingerprint="sha256:test-client",
        scopes=[AgentScope.WRITE_TASKS_TRANSFER],
        expires_at=timezone.now() + timedelta(days=1),
    )
    request_id = uuid4()
    AgentActionLog.objects.create(
        grant=grant,
        company=company,
        request_id=request_id,
        tool_name="tasks.transfer",
        required_scope=AgentScope.WRITE_TASKS_TRANSFER,
        idempotency_key="idem-1",
        arguments_hash=arguments_hash({"task_id": "task-1", "to_user_id": "user-2"}),
    )

    event = record_audit_event(
        event_type="TASK_TRANSFERRED",
        actor_id=str(user.id),
        target_type="task",
        target_id="task-1",
        request_id=request_id,
    )

    trail = get_audit_trail(request_id=request_id)

    assert [entry.id for entry in trail] == [event.id]
    assert trail[0].executed_via == "agent"
    assert trail[0].agent_tool_name == "tasks.transfer"
    assert trail[0].agent_grant_id == str(grant.id)


@pytest.mark.django_db
def test_get_audit_trail_marks_human_events_without_agent_log(make_user) -> None:
    user = make_user()
    request_id = uuid4()
    record_audit_event(
        event_type="TASK_UPDATED",
        actor_id=str(user.id),
        target_type="task",
        target_id="task-1",
        request_id=request_id,
    )

    trail = get_audit_trail(request_id=request_id)

    assert len(trail) == 1
    assert trail[0].executed_via == "human"
    assert trail[0].agent_tool_name is None
    assert trail[0].agent_grant_id is None
