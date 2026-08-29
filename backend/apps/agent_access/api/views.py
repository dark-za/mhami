from __future__ import annotations

import json
from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..mcp import call_tool, list_tools_for_grant
from ..security import verify_mcp_hmac


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
