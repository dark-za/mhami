from __future__ import annotations

from rest_framework import serializers

from .models import CaptureSession, EvidenceItem, EvidenceType, TaskDiscussionMessage, TaskIssueReport


class CaptureSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaptureSession
        fields = [
            "id",
            "company",
            "branch",
            "task_instance",
            "template_version",
            "created_by",
            "evidence_type",
            "token",
            "challenge_text",
            "status",
            "expires_at",
            "used_at",
        ]


class CaptureSessionCreateSerializer(serializers.Serializer):
    task_instance_id = serializers.UUIDField()
    evidence_type = serializers.ChoiceField(choices=EvidenceType.choices)
    challenge_answer = serializers.CharField(required=False, allow_blank=True)


class EvidenceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = [
            "id",
            "company",
            "branch",
            "task_instance",
            "capture_session",
            "submitted_by",
            "evidence_type",
            "status",
            "sequence_number",
            "parent_submission",
            "note_text",
            "number_value",
            "confirmation_value",
            "quarantine_name",
            "private_media_name",
            "blurred_media_name",
            "media_mime_type",
            "media_size_bytes",
            "media_width",
            "media_height",
            "raw_hash",
            "derivative_hash",
            "duplicate_risk_score",
            "face_detected",
            "challenge_response",
            "metadata",
            "created_at",
        ]


class EvidenceSubmitSerializer(serializers.Serializer):
    capture_token = serializers.CharField()
    note_text = serializers.CharField(required=False, allow_blank=True)
    number_value = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    confirmation_value = serializers.BooleanField(required=False)
    face_detected = serializers.BooleanField(required=False, default=False)
    challenge_response = serializers.CharField(required=False, allow_blank=True)


class TaskIssueReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskIssueReport
        fields = [
            "id",
            "company",
            "branch",
            "task_instance",
            "submitted_by",
            "note",
            "photo_name",
            "resolved_at",
            "resolution_note",
            "created_at",
        ]


class TaskIssueCreateSerializer(serializers.Serializer):
    task_instance_id = serializers.UUIDField()
    note = serializers.CharField()


class TaskDiscussionMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDiscussionMessage
        fields = [
            "id",
            "company",
            "branch",
            "task_instance",
            "issue_report",
            "reply_to",
            "author",
            "message",
            "created_at",
        ]


class TaskDiscussionCreateSerializer(serializers.Serializer):
    task_instance_id = serializers.UUIDField()
    issue_report_id = serializers.UUIDField(required=False)
    reply_to_id = serializers.UUIDField(required=False)
    message = serializers.CharField()
