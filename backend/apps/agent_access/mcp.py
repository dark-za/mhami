from __future__ import annotations

import json
from collections.abc import Callable, Mapping

from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework.exceptions import ParseError

from apps.tasks.models import TaskInstance
from apps.tasks.serializers import TaskInstanceSerializer, TaskTransferRequestSerializer
from apps.tasks.services import request_transfer

from .models import AgentActionStatus, AgentGrant
from .services import record_agent_action


class McpTool:
    def __init__(
        self,
        *,
        name: str,
        description: str,
        required_scope: str,
        input_schema: dict[str, object],
        handler: Callable[[AgentGrant, Mapping[str, object]], object],
    ) -> None:
        self.name = name
        self.description = description
        self.required_scope = required_scope
        self.input_schema = input_schema
        self.handler = handler

    def descriptor(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "requiredScope": self.required_scope,
        }


def _require_string(arguments: Mapping[str, object], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value:
        raise ParseError(f"{key} is required.")
    return value


def _system_describe(grant: AgentGrant, arguments: Mapping[str, object]) -> dict[str, object]:
    return {
        "service": "mhami-mcp",
        "protocolVersion": "2026-07-28",
        "companyId": str(grant.company_id),
        "grantId": str(grant.id),
        "scopes": grant.scopes,
    }


def _tasks_list(grant: AgentGrant, arguments: Mapping[str, object]) -> dict[str, object]:
    queryset = (
        TaskInstance.objects.filter(company=grant.company)
        .select_related("template", "branch", "assigned_user")
        .order_by("-scheduled_for", "-created_at")
    )
    status = arguments.get("status")
    if isinstance(status, str) and status:
        queryset = queryset.filter(status=status)
    limit = arguments.get("limit", 50)
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ParseError("limit must be an integer from 1 to 100.")
    return {"tasks": TaskInstanceSerializer(queryset[:limit], many=True).data}


def _tasks_transfer_request(grant: AgentGrant, arguments: Mapping[str, object]) -> dict[str, object]:
    task_id = _require_string(arguments, "task_id")
    requested_to_id = _require_string(arguments, "requested_to_id")
    reason = arguments.get("reason", "")
    if not isinstance(reason, str):
        raise ParseError("reason must be a string.")
    instance = TaskInstance.objects.filter(id=task_id, company=grant.company).first()
    if instance is None:
        raise PermissionDenied("Task is outside the MCP grant company.")
    requested_to = get_user_model().objects.filter(id=requested_to_id).first()
    if requested_to is None:
        raise PermissionDenied("Transfer target does not exist in this company.")
    transfer = request_transfer(str(instance.id), grant.user, requested_to, reason)
    return {"transfer": TaskTransferRequestSerializer(transfer).data}


TOOLS: dict[str, McpTool] = {
    "system.describe": McpTool(
        name="system.describe",
        description="Describe the Mhami MCP server and active grant.",
        required_scope="read:reports",
        input_schema={"type": "object", "additionalProperties": False, "properties": {}},
        handler=_system_describe,
    ),
    "tasks.list": McpTool(
        name="tasks.list",
        description="List task instances in the grant company.",
        required_scope="read:tasks",
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
        },
        handler=_tasks_list,
    ),
    "tasks.transfer.request": McpTool(
        name="tasks.transfer.request",
        description="Request a task transfer to another company user.",
        required_scope="write:tasks:transfer",
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["task_id", "requested_to_id"],
            "properties": {
                "task_id": {"type": "string"},
                "requested_to_id": {"type": "string"},
                "reason": {"type": "string"},
            },
        },
        handler=_tasks_transfer_request,
    ),
}


def _json_safe(value: object) -> dict[str, object]:
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


def list_tools_for_grant(grant: AgentGrant) -> list[dict[str, object]]:
    return [
        tool.descriptor()
        for tool in TOOLS.values()
        if tool.required_scope in grant.scopes or "admin:full" in grant.scopes
    ]


def call_tool(
    *,
    grant: AgentGrant,
    name: str,
    arguments: Mapping[str, object],
    idempotency_key: str,
    request_id,
) -> dict[str, object]:
    tool = TOOLS.get(name)
    if tool is None:
        raise ParseError("Unknown MCP tool.")
    action_log, created = record_agent_action(
        grant=grant,
        tool_name=name,
        required_scope=tool.required_scope,
        idempotency_key=idempotency_key,
        arguments=arguments,
        request_id=request_id,
    )
    if not created and action_log.status == AgentActionStatus.EXECUTED:
        return {"replayed": True, "result": action_log.result}
    if not created:
        raise ValidationError({"idempotency_key": "MCP action is already in progress."})
    try:
        result = tool.handler(grant, arguments)
    except Exception as exc:
        action_log.status = AgentActionStatus.FAILED
        action_log.error_code = exc.__class__.__name__
        action_log.save(update_fields=["status", "error_code", "updated_at"])
        raise
    action_log.status = AgentActionStatus.EXECUTED
    action_log.result = _json_safe(result)
    action_log.save(update_fields=["status", "result", "updated_at"])
    return {"replayed": False, "result": action_log.result}
