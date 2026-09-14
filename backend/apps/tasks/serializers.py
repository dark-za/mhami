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
    TaskRequest,
    TaskRequestKind,
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
    name = serializers.CharField(source="template.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    assigned_user_name = serializers.SerializerMethodField()

    def get_assigned_user_name(self, instance: TaskInstance) -> str:
        if instance.assigned_user is None:
            return ""
        return instance.assigned_user.display_name or instance.assigned_user.login_id

    class Meta:
        model = TaskInstance
        fields = [
            "id",
            "name",
            "branch_name",
            "assigned_user_name",
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
    task_name = serializers.CharField(source="task_instance.template.name", read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    requested_to_name = serializers.SerializerMethodField()

    def get_requested_by_name(self, transfer: TaskTransferRequest) -> str:
        return transfer.requested_by.display_name or transfer.requested_by.login_id

    def get_requested_to_name(self, transfer: TaskTransferRequest) -> str:
        return transfer.requested_to.display_name or transfer.requested_to.login_id

    class Meta:
        model = TaskTransferRequest
        fields = [
            "id",
            "task_name",
            "task_instance",
            "requested_by",
            "requested_by_name",
            "requested_to",
            "requested_to_name",
            "status",
            "reason",
            "decided_by",
            "decided_at",
        ]


class TaskTransferRecipientSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    display_name = serializers.CharField()


class TaskRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskRequest
        fields = [
            "id",
            "company",
            "branch",
            "task_instance",
            "requested_by",
            "requested_to",
            "kind",
            "reason",
            "status",
            "decision_reason",
            "decided_by",
            "decided_at",
            "created_at",
            "updated_at",
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


class ScheduledTaskCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    slug = serializers.SlugField(max_length=96, required=False)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    assigned_user_id = serializers.UUIDField()
    instructions = serializers.CharField()
    checklist_definition = serializers.ListField(child=serializers.JSONField(), required=False)
    evidence_requirements = serializers.ListField(child=serializers.JSONField(), required=False)
    reference_instructions = serializers.CharField(required=False, allow_blank=True)
    risk_level = serializers.ChoiceField(choices=TaskRiskLevel.choices, required=False)
    task_weight = serializers.IntegerField(required=False, min_value=1)
    recurrence_type = serializers.ChoiceField(choices=TaskRecurrenceType.choices)
    scheduled_time = serializers.TimeField(required=False, allow_null=True)
    weekday = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=6)
    shift_offset_minutes = serializers.IntegerField(required=False, default=0)


class TaskTransitionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)
    requested_to_id = serializers.UUIDField(required=False)
    approved = serializers.BooleanField(required=False)


class TaskRequestCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    task_instance_id = serializers.UUIDField(required=False, allow_null=True)
    requested_to_id = serializers.UUIDField(required=False, allow_null=True)
    kind = serializers.ChoiceField(choices=TaskRequestKind.choices)
    reason = serializers.CharField(max_length=2000)


class TaskRequestDecisionSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    decision_reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)
