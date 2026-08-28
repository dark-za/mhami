"""DRF serializers for the compliance module."""

from __future__ import annotations

from rest_framework import serializers

from .models import DSRRequest, DSRRequestStatus, DSRRequestType, LegalDocument, ProcessingActivity


class ProcessingActivitySerializer(serializers.ModelSerializer):
    """Serializer for :class:`ProcessingActivity` rows."""

    class Meta:
        model = ProcessingActivity
        fields = [
            "id",
            "name",
            "purpose",
            "controller",
            "processor",
            "data_categories",
            "data_subject_categories",
            "recipients",
            "lawful_basis",
            "cross_border_transfer",
            "transfer_mechanism",
            "retention_days",
            "security_measures",
            "last_reviewed_at",
            "published_at",
        ]
        read_only_fields = fields


class DSRRequestCreateSerializer(serializers.Serializer):
    """Inbound payload for ``POST /api/v1/compliance/dsr``."""

    request_type = serializers.ChoiceField(choices=DSRRequestType.choices)
    subject_email = serializers.EmailField()
    subject_reference = serializers.CharField(max_length=200, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class DSRRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DSRRequest
        fields = [
            "id",
            "request_type",
            "subject_email",
            "subject_reference",
            "description",
            "status",
            "decision_notes",
            "decided_at",
            "submitted_at",
            "updated_at",
        ]
        read_only_fields = fields


class DSRDecisionSerializer(serializers.Serializer):
    """Inbound payload for DSR state transitions (verify/start/etc)."""

    notes = serializers.CharField(required=False, allow_blank=True)


class DSRRejectionSerializer(serializers.Serializer):
    """Inbound payload for ``POST /dsr/<id>/reject``."""

    reason = serializers.CharField(max_length=2000)


class LegalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocument
        fields = [
            "id",
            "kind",
            "version",
            "content_path",
            "summary",
            "effective_date",
            "supersedes_version",
            "published_at",
            "is_current",
        ]
        read_only_fields = fields


class DSRStatusFilterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=DSRRequestStatus.choices, required=False)
