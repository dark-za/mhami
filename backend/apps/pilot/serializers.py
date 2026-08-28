from __future__ import annotations

from rest_framework import serializers

from .models import PilotChangeRequest, PilotCharter, PilotIssue, PilotProgram, PilotWeeklyReport


class PilotProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilotProgram
        fields = [
            "id",
            "company",
            "status",
            "branch_count_target",
            "employee_count_target",
            "chrome_device_count",
            "ai_provider_name",
            "connector_owner",
            "test_environment",
            "success_measures",
            "escalation_contacts",
            "operating_checklist",
            "weekly_metrics_goal",
            "notes",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class PilotProgramUpdateSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    branch_count_target = serializers.IntegerField(required=False, min_value=1)
    employee_count_target = serializers.IntegerField(required=False, min_value=1)
    chrome_device_count = serializers.IntegerField(required=False, min_value=0)
    ai_provider_name = serializers.CharField(required=False, allow_blank=True)
    connector_owner = serializers.CharField(required=False, allow_blank=True)
    test_environment = serializers.CharField(required=False, allow_blank=True)
    success_measures = serializers.ListField(child=serializers.CharField(), required=False)
    escalation_contacts = serializers.ListField(child=serializers.CharField(), required=False)
    operating_checklist = serializers.ListField(child=serializers.CharField(), required=False)
    weekly_metrics_goal = serializers.JSONField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class PilotDashboardProgramSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    company = serializers.UUIDField()
    status = serializers.CharField()
    branch_count_target = serializers.IntegerField()
    employee_count_target = serializers.IntegerField()
    chrome_device_count = serializers.IntegerField()
    ai_provider_name = serializers.CharField()
    connector_owner = serializers.CharField()
    test_environment = serializers.CharField()
    success_measures = serializers.ListField(child=serializers.CharField())
    escalation_contacts = serializers.ListField(child=serializers.CharField())
    operating_checklist = serializers.ListField(child=serializers.CharField())
    weekly_metrics_goal = serializers.JSONField()
    notes = serializers.CharField()


class PilotDashboardSummarySerializer(serializers.Serializer):
    evidence_items_week = serializers.IntegerField()
    image_evidence_week = serializers.IntegerField()
    face_blurred_week = serializers.IntegerField()
    ai_runs_week = serializers.IntegerField()
    ai_agreement_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    backup_completed = serializers.BooleanField()
    connector_status = serializers.CharField()
    connector_health = serializers.CharField()
    exports_completed = serializers.IntegerField()
    reviews_created = serializers.IntegerField()


class PilotDashboardCountsSerializer(serializers.Serializer):
    issues = serializers.IntegerField()
    change_requests = serializers.IntegerField()
    reports = serializers.IntegerField()


class PilotCharterSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    pilot_program = serializers.UUIDField()
    decision = serializers.CharField()
    rationale = serializers.CharField()
    conditions = serializers.CharField()
    observation_start = serializers.DateField(allow_null=True)
    observation_end = serializers.DateField(allow_null=True)
    success_measures = serializers.ListField(child=serializers.CharField())
    signed_by = serializers.UUIDField()
    signed_at = serializers.DateTimeField()
    signature_valid = serializers.BooleanField()


class PilotDashboardSerializer(serializers.Serializer):
    program = PilotDashboardProgramSerializer()
    summary = PilotDashboardSummarySerializer()
    counts = PilotDashboardCountsSerializer()
    charter = PilotCharterSummarySerializer(allow_null=True)
    program_id = serializers.UUIDField()


class PilotWeeklyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilotWeeklyReport
        fields = [
            "id",
            "pilot_program",
            "week_ending",
            "metrics",
            "ai_agreement_rate",
            "error_analysis",
            "capacity_findings",
            "created_by",
            "created_at",
        ]


class PilotWeeklyReportCreateSerializer(serializers.Serializer):
    week_ending = serializers.DateField()
    metrics = serializers.JSONField(required=False)
    ai_agreement_rate = serializers.DecimalField(required=False, max_digits=5, decimal_places=2)
    error_analysis = serializers.CharField(required=False, allow_blank=True)
    capacity_findings = serializers.CharField(required=False, allow_blank=True)


class PilotWeeklyReportListSerializer(serializers.Serializer):
    reports = PilotWeeklyReportSerializer(many=True)


class PilotIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilotIssue
        fields = ["id", "pilot_program", "title", "severity", "status", "details", "created_by", "created_at"]


class PilotIssueCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    severity = serializers.CharField(required=False, default="medium")
    details = serializers.CharField(required=False, allow_blank=True)


class PilotIssueUpdateSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    details = serializers.CharField(required=False, allow_blank=True)


class PilotIssueListSerializer(serializers.Serializer):
    issues = PilotIssueSerializer(many=True)


class PilotChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PilotChangeRequest


class PilotCharterSerializer(serializers.ModelSerializer):
    signature_valid = serializers.SerializerMethodField()

    class Meta:
        model = PilotCharter
        fields = [
            "id",
            "pilot_program",
            "company",
            "decision",
            "rationale",
            "conditions",
            "observation_start",
            "observation_end",
            "success_measures",
            "signed_by",
            "signed_at",
            "signature_hmac",
            "signature_valid",
            "metadata",
        ]

    def get_signature_valid(self, obj: PilotCharter) -> bool:
        return obj.verify_signature()


class PilotCharterCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=PilotCharter.Decision.choices)
    rationale = serializers.CharField()
    conditions = serializers.CharField(required=False, allow_blank=True)
    observation_start = serializers.DateField(required=False, allow_null=True)
    observation_end = serializers.DateField(required=False, allow_null=True)
    success_measures = serializers.ListField(child=serializers.CharField(), required=False)
    metadata = serializers.JSONField(required=False)


class PilotChangeRequestCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    rationale = serializers.CharField(required=False, allow_blank=True)


class PilotChangeRequestUpdateSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    rationale = serializers.CharField(required=False, allow_blank=True)


class PilotChangeRequestListSerializer(serializers.Serializer):
    change_requests = PilotChangeRequestSerializer(many=True)
