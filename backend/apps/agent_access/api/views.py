from __future__ import annotations

import json
from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from django.shortcuts import get_object_or_404
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import CompanyRole
from apps.platform_core.errors import platform_service_call
from apps.platform_core.mixins import TenantAPIView

from ..models import AgentActionLog, AgentGrant
from ..mcp import call_tool, list_tools_for_grant
from ..serializers import (
    AgentActionLogListSerializer,
    AgentActionLogSerializer,
    AgentGrantCreateSerializer,
    AgentGrantListSerializer,
    AgentGrantRevokeSerializer,
    AgentGrantSerializer,
    AgentScopeSerializer,
)
from ..security import verify_mcp_hmac
from ..services import create_agent_grant, revoke_agent_grant


def _jsonrpc_response(request_id: object, result: object) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


class McpEndpointView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=dict,
        responses={200: OpenApiResponse(response=dict, description="MCP JSON-RPC response.")},
        examples=[
            OpenApiExample(
                "MCP tools list",
                value={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        verified = verify_mcp_hmac(request.headers, request.body)
        try:
            payload: dict[str, Any] = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ParseError("Invalid MCP JSON-RPC payload.") from exc
        rpc_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params") or {}
        if not isinstance(params, dict):
            raise ParseError("MCP params must be an object.")

        if method == "initialize":
            return Response(
                _jsonrpc_response(
                    rpc_id,
                    {
                        "protocolVersion": "2026-07-28",
                        "serverInfo": {"name": "mhami-mcp", "version": "0.1.0"},
                        "capabilities": {"tools": {"listChanged": False}},
                    },
                )
            )
        if method == "tools/list":
            return Response(_jsonrpc_response(rpc_id, {"tools": list_tools_for_grant(verified.grant)}))
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            idempotency_key = params.get("idempotency_key")
            if not isinstance(name, str) or not name:
                raise ParseError("MCP tool name is required.")
            if not isinstance(arguments, dict):
                raise ParseError("MCP tool arguments must be an object.")
            if not isinstance(idempotency_key, str) or not idempotency_key:
                raise ParseError("MCP idempotency_key is required for tool calls.")
            result = call_tool(
                grant=verified.grant,
                name=name,
                arguments=arguments,
                idempotency_key=idempotency_key,
                request_id=verified.request_id,
            )
            return Response(_jsonrpc_response(rpc_id, result))
        raise ParseError("Unsupported MCP method.")


class AgentScopeListView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=AgentScopeSerializer)
    def get(self, request):
        self.get_tenant()
        return Response(AgentScopeSerializer({}).data)


class AgentGrantListCreateView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(
        operation_id="agent_grants_list",
        responses=AgentGrantListSerializer,
    )
    @platform_service_call
    def get(self, request):
        company = self.get_tenant().company
        grants = AgentGrant.objects.filter(company=company).select_related("user").order_by("-created_at")
        return Response({"grants": AgentGrantSerializer(grants, many=True).data})

    @extend_schema(
        operation_id="agent_grants_create",
        request=AgentGrantCreateSerializer,
        responses={201: AgentGrantSerializer},
    )
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        serializer = AgentGrantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grant = create_agent_grant(
            owner_id=request.user.id,
            company=company,
            user_id=serializer.validated_data["user_id"],
            client_name=serializer.validated_data["client_name"],
            client_fingerprint=serializer.validated_data["client_fingerprint"],
            scopes=list(serializer.validated_data["scopes"]),
            expires_at=serializer.validated_data["expires_at"],
        )
        return Response(AgentGrantSerializer(grant).data, status=201)


class AgentGrantDetailView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)

    def _grant(self, grant_id: str) -> AgentGrant:
        company = self.get_tenant().company
        return get_object_or_404(
            AgentGrant.objects.select_related("company", "user"),
            id=grant_id,
            company=company,
        )

    @extend_schema(operation_id="agent_grants_retrieve", responses=AgentGrantSerializer)
    @platform_service_call
    def get(self, request, grant_id):
        return Response(AgentGrantSerializer(self._grant(grant_id)).data)


class AgentGrantRevokeView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(
        operation_id="agent_grants_revoke",
        request=AgentGrantRevokeSerializer,
        responses=AgentGrantSerializer,
    )
    @platform_service_call
    def post(self, request, grant_id):
        company = self.get_tenant().company
        grant = get_object_or_404(AgentGrant.objects.select_related("company"), id=grant_id, company=company)
        serializer = AgentGrantRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grant = revoke_agent_grant(
            owner_id=request.user.id,
            grant=grant,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(AgentGrantSerializer(grant).data)


class AgentActionLogListView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(
        operation_id="agent_action_logs_list",
        responses=AgentActionLogListSerializer,
    )
    @platform_service_call
    def get(self, request):
        company = self.get_tenant().company
        logs = (
            AgentActionLog.objects.filter(company=company)
            .select_related("grant")
            .order_by("-created_at")[:100]
        )
        return Response({"logs": AgentActionLogSerializer(logs, many=True).data})
