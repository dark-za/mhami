from __future__ import annotations

from rest_framework import serializers

from .models import ConnectorHealthStatus, TenantConnectorEnrollment


class TenantConnectorEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantConnectorEnrollment
        fields = [
            "id",
            "company",
            "connector_version",
            "compatibility_window",
            "status",
            "health_status",
            "last_seen_at",
            "health_expires_at",
            "health_ttl_seconds",
            "revoked_at",
            "created_by",
            "created_at",
            "updated_at",
        ]


class TenantConnectorEnrollSerializer(serializers.Serializer):
    connector_version = serializers.CharField()
    shared_secret_fingerprint = serializers.RegexField(regex=r"^[0-9a-fA-F]{64}$")
    health_ttl_seconds = serializers.IntegerField(required=False, min_value=30, max_value=86_400)


class TenantConnectorRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class ConnectorHeartbeatSerializer(serializers.Serializer):
    enrollment_id = serializers.UUIDField()
    connector_version = serializers.CharField(max_length=64)
    provider_status = serializers.ChoiceField(choices=ConnectorHealthStatus.choices)
