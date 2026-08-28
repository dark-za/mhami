from __future__ import annotations

from rest_framework import serializers

from .models import BackupPolicy, BackupRun, RestoreRun


class BackupPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupPolicy
        fields = [
            "id",
            "company",
            "destination_name",
            "encrypted",
            "schedule_cron",
            "rpo_hours",
            "rto_hours",
            "includes_private_media",
            "includes_configuration",
            "includes_tenant_state",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class BackupPolicyUpdateSerializer(serializers.Serializer):
    destination_name = serializers.CharField(required=False)
    encrypted = serializers.BooleanField(required=False)
    schedule_cron = serializers.CharField(required=False)
    rpo_hours = serializers.IntegerField(required=False, min_value=1)
    rto_hours = serializers.IntegerField(required=False, min_value=1)
    includes_private_media = serializers.BooleanField(required=False)
    includes_configuration = serializers.BooleanField(required=False)
    includes_tenant_state = serializers.BooleanField(required=False)


class BackupRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRun
        fields = [
            "id",
            "company",
            "requested_by",
            "status",
            "artifact_name",
            "artifact_sha256",
            "manifest_sha256",
            "manifest",
            "error_message",
            "started_at",
            "completed_at",
            "restored_at",
        ]


class BackupCreateSerializer(serializers.Serializer):
    include_private_media = serializers.BooleanField(required=False, default=True)
    include_configuration = serializers.BooleanField(required=False, default=True)
    include_tenant_state = serializers.BooleanField(required=False, default=True)


class RestoreRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestoreRun
        fields = [
            "id",
            "company",
            "backup_run",
            "requested_by",
            "status",
            "verified_database",
            "verified_media",
            "verified_configuration",
            "target_name",
            "report",
            "created_at",
            "completed_at",
        ]


class RestoreCreateSerializer(serializers.Serializer):
    backup_run_id = serializers.UUIDField()
    target_name = serializers.RegexField(regex=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
    confirmation = serializers.CharField(max_length=128)
