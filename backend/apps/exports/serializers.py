from __future__ import annotations

from rest_framework import serializers

from .models import ExportBoundaryPolicy, ExportRequest, ExportType


class ExportBoundaryPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportBoundaryPolicy
        fields = [
            "id",
            "company",
            "future_notification_boundaries",
            "external_storage_boundaries",
            "provider_review_checklist",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class ExportBoundaryPolicyUpdateSerializer(serializers.Serializer):
    future_notification_boundaries = serializers.ListField(child=serializers.CharField(), required=False)
    external_storage_boundaries = serializers.ListField(child=serializers.CharField(), required=False)
    provider_review_checklist = serializers.ListField(child=serializers.CharField(), required=False)


class ExportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportRequest
        fields = [
            "id",
            "company",
            "requested_by",
            "export_type",
            "branch_ids",
            "categories",
            "start_date",
            "end_date",
            "status",
            "download_token",
            "file_name",
            "expires_at",
            "completed_at",
            "downloaded_at",
            "last_error",
            "created_at",
            "updated_at",
        ]


class ExportRequestCreateSerializer(serializers.Serializer):
    export_type = serializers.ChoiceField(choices=ExportType.choices)
    branch_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
