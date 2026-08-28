from __future__ import annotations

from rest_framework import serializers

from apps.platform_core.models import ExitDecision


class BootstrapCurrentUserSerializer(serializers.Serializer):
    is_authenticated = serializers.BooleanField()
    id = serializers.CharField(allow_null=True)
    login_id = serializers.CharField(allow_null=True)
    display_name = serializers.CharField(allow_null=True)


class BootstrapCompanySerializer(serializers.Serializer):
    id = serializers.CharField(allow_null=True)
    name = serializers.CharField(allow_null=True)
    code = serializers.CharField(allow_null=True)
    status = serializers.CharField(allow_null=True)
    industry = serializers.CharField(allow_null=True)


class BootstrapBranchSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    code = serializers.CharField()
    timezone = serializers.CharField()
    operational_day_cutoff = serializers.CharField()
    active = serializers.BooleanField()


class BootstrapSerializer(serializers.Serializer):
    current_user = BootstrapCurrentUserSerializer()
    company = BootstrapCompanySerializer(allow_null=True)
    permissions = serializers.ListField(child=serializers.CharField())
    branches = BootstrapBranchSerializer(many=True)
    enabled_modules = serializers.ListField(child=serializers.CharField())
    feature_flags = serializers.ListField(child=serializers.DictField())
    app_version = serializers.CharField()


class ExitDecisionCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ExitDecision.Decision.choices)
    rationale = serializers.CharField(min_length=10, max_length=4000, trim_whitespace=True)
    supersedes = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False)


class ExitDecisionSerializer(serializers.ModelSerializer):
    signed_by_login = serializers.CharField(source="signed_by.login_id", read_only=True)

    class Meta:
        model = ExitDecision
        fields = [
            "id",
            "phase",
            "decision",
            "rationale",
            "signed_by",
            "signed_by_login",
            "signed_at",
            "supersedes",
            "signature_hmac",
            "metadata",
        ]
        read_only_fields = ["signed_by", "signed_at", "signature_hmac"]
