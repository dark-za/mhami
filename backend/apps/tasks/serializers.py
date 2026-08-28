from __future__ import annotations

from rest_framework import serializers

from .models import (
    TaskAssignmentMode,
    TaskInstance,
    TaskRecurrenceType,
    TaskRiskLevel,
    TaskSchedule,
    TaskTemplate,
    TaskTemplateVersion,
    TaskTransferRequest,
)


class TaskTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTemplate
        fields = [
            "id",
            "company",
            "branch",
            "slug",
            "name",
            "description",
            "assignment_mode",
            "assigned_user",
            "assigned_role_code",
            "risk_level",
            "task_weight",
            "active",
        ]


class TaskTemplateVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTemplateVersion
        fields = [
            "id",
            "template",
            "version_number",
            "instructions",
            "checklist_definition",
            "evidence_requirements",
            "reference_instructions",
            "risk_level",
            "created_at",
        ]


class TaskScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSchedule
        fields = [
            "id",
            "company",
            "branch",
            "template",
            "recurrence_type",
            "scheduled_time",
            "weekday",
            "shift_offset_minutes",
            "active",
            "last_generated_at",
        ]


class TaskInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskInstance
        fields = [
            "id",
            "company",
            "branch",
            "template",
            "template_version",
            "schedule",
            "scheduled_for",
            "due_at",
            "status",
            "assigned_user",
            "claimed_by",
            "started_at",
            "completed_at",
            "cancelled_at",
            "overdue_at",
            "cancel_reason",
        ]


class TaskTransferRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTransferRequest
        fields = [
            "id",
            "task_instance",
            "requested_by",
            "requested_to",
            "status",
            "reason",
            "decided_by",
            "decided_at",
        ]


class TaskTemplateCreateSerializer(serializers.Serializer):
    company_id = serializers.UUIDField()
    branch_id = serializers.UUIDField(required=False)
    slug = serializers.SlugField(max_length=96)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    assignment_mode = serializers.ChoiceField(choices=TaskAssignmentMode.choices)
    assigned_user_id = serializers.UUIDField(required=False)
    assigned_role_code = serializers.CharField(max_length=64, required=False, allow_blank=True)
    risk_level = serializers.ChoiceField(choices=TaskRiskLevel.choices, required=False)
    task_weight = serializers.IntegerField(required=False, min_value=1)


class TaskTemplateVersionCreateSerializer(serializers.Serializer):
    template_id = serializers.UUIDField()
    version_number = serializers.IntegerField(min_value=1)
    instructions = serializers.CharField()
    checklist_definition = serializers.ListField(child=serializers.JSONField(), required=False)
    evidence_requirements = serializers.ListField(child=serializers.JSONField(), required=False)
    reference_instructions = serializers.CharField(required=False, allow_blank=True)
    risk_level = serializers.ChoiceField(choices=TaskRiskLevel.choices, required=False)


class TaskScheduleCreateSerializer(serializers.Serializer):
    company_id = serializers.UUIDField()
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    template_id = serializers.UUIDField()
    recurrence_type = serializers.ChoiceField(choices=TaskRecurrenceType.choices)
    scheduled_time = serializers.TimeField(required=False, allow_null=True)
    weekday = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=6)
    shift_offset_minutes = serializers.IntegerField(required=False, default=0)


class TaskTransitionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)
    requested_to_id = serializers.UUIDField(required=False)
    approved = serializers.BooleanField(required=False)
