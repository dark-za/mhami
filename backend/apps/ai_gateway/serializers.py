from __future__ import annotations

from rest_framework import serializers

from .models import AIAnalysisCriterion, AIAnalysisRun, AIProviderConfig


class AIProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProviderConfig
        fields = [
            "id",
            "company",
            "provider_name",
            "endpoint_url",
            "model_name",
            "credential_reference",
            "monthly_token_limit",
            "monthly_cost_limit",
            "enabled",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class AIProviderConfigUpdateSerializer(serializers.Serializer):
    provider_name = serializers.CharField(required=False)
    endpoint_url = serializers.CharField(required=False, allow_blank=True)
    model_name = serializers.CharField(required=False, allow_blank=True)
    credential_reference = serializers.CharField(required=False, allow_blank=True)
    monthly_token_limit = serializers.IntegerField(required=False, min_value=1)
    monthly_cost_limit = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    enabled = serializers.BooleanField(required=False)


class AIAnalysisCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAnalysisCriterion
        fields = [
            "id",
            "company",
            "version_number",
            "title",
            "criteria_json",
            "reference_media_names",
            "shadow_mode",
            "auto_pass_enabled",
            "auto_pass_risk_threshold",
            "active",
            "created_by",
            "created_at",
        ]


class AIAnalysisCriterionCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    criteria_json = serializers.JSONField(required=False)
    reference_media_names = serializers.ListField(child=serializers.CharField(), required=False)
    shadow_mode = serializers.BooleanField(required=False, default=True)
    auto_pass_enabled = serializers.BooleanField(required=False, default=False)
    auto_pass_risk_threshold = serializers.IntegerField(required=False, min_value=1, max_value=100)

    def validate(self, attrs):
        if attrs.get("shadow_mode") is False:
            raise serializers.ValidationError({"shadow_mode": "AI must remain in Shadow Mode."})
        if attrs.get("auto_pass_enabled") is True:
            raise serializers.ValidationError({"auto_pass_enabled": "AI auto-pass is not available."})
        return attrs


class AIAnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAnalysisRun
        fields = [
            "id",
            "company",
            "branch",
            "evidence_item",
            "provider_name",
            "model_name",
            "prompt_version",
            "status",
            "shadow_mode",
            "auto_pass_eligible",
            "auto_pass_activated",
            "risk_level",
            "provider_payload",
            "provider_result",
            "human_decision",
            "agreement_with_human",
            "review_decision",
            "error_message",
            "reviewed_at",
            "created_by",
            "created_at",
        ]


class AIAnalysisRunCreateSerializer(serializers.Serializer):
    evidence_item_id = serializers.UUIDField()
    criterion_id = serializers.UUIDField(required=False)
