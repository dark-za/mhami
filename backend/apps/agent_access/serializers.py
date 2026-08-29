from __future__ import annotations

from rest_framework import serializers

from .models import (
    AgentActionLog,
    AgentGrant,
    active_agent_scope_values,
)


class AgentGrantSerializer(serializers.ModelSerializer):
    active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AgentGrant
        fields = [
            "id",
            "company",
            "user",
            "client_name",
            "client_fingerprint",
            "scopes",
            "status",
            "active",
            "expires_at",
            "revoked_at",
            "created_at",
            "updated_at",
        ]


class AgentGrantCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    client_name = serializers.CharField(max_length=160)
    client_fingerprint = serializers.RegexField(
        regex=r"^sha256:[0-9a-fA-F]{64}$",
        max_length=128,
    )
    scopes = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(active_agent_scope_values())),
        allow_empty=False,
    )
    expires_at = serializers.DateTimeField()


class AgentGrantRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class AgentGrantListSerializer(serializers.Serializer):
    grants = AgentGrantSerializer(many=True)


class AgentActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentActionLog
        fields = [
            "id",
            "grant",
            "company",
            "request_id",
            "tool_name",
            "required_scope",
            "idempotency_key",
            "arguments_hash",
            "status",
            "result",
            "error_code",
            "created_at",
            "updated_at",
        ]


class AgentActionLogListSerializer(serializers.Serializer):
    logs = AgentActionLogSerializer(many=True)


class AgentScopeSerializer(serializers.Serializer):
    scopes = serializers.SerializerMethodField()

    def get_scopes(self, obj: object) -> list[dict[str, str]]:
        return [
            {"value": value, "status": "active"}
            for value in sorted(active_agent_scope_values())
        ]
