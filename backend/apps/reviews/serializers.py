from __future__ import annotations

from rest_framework import serializers

from .models import ReviewDecision, ReviewDecisionType, ReviewPolicySetting


class ReviewPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewPolicySetting
        fields = [
            "id",
            "company",
            "employee_score_visibility",
            "historical_report_restatement",
            "monitor_approval_required",
            "sensitive_task_claim_restricted",
            "extra_evidence_required",
            "owner_alerts_enabled",
            "approved_task_weight_cap",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class ReviewPolicyUpdateSerializer(serializers.Serializer):
    employee_score_visibility = serializers.ChoiceField(choices=[("hidden", "hidden"), ("summary", "summary"), ("detailed", "detailed")], required=False)
    historical_report_restatement = serializers.BooleanField(required=False)
    monitor_approval_required = serializers.BooleanField(required=False)
    sensitive_task_claim_restricted = serializers.BooleanField(required=False)
    extra_evidence_required = serializers.BooleanField(required=False)
    owner_alerts_enabled = serializers.BooleanField(required=False)
    approved_task_weight_cap = serializers.IntegerField(required=False, min_value=1)


class ReviewDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewDecision
        fields = [
            "id",
            "company",
            "branch",
            "decided_by",
            "decision_type",
            "reason",
            "task_instance",
            "evidence_item",
            "issue_report",
            "generated_task_instance",
            "restriction_name",
            "original_status",
            "resulting_status",
            "metadata",
            "created_at",
        ]


class ReviewDecisionCreateSerializer(serializers.Serializer):
    decision_type = serializers.ChoiceField(choices=ReviewDecisionType.choices)
    reason = serializers.CharField(required=False, allow_blank=True)
    task_instance_id = serializers.UUIDField(required=False)
    evidence_item_id = serializers.UUIDField(required=False)
    issue_report_id = serializers.UUIDField(required=False)
    restriction_name = serializers.CharField(required=False, allow_blank=True)
