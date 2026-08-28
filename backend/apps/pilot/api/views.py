from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from apps.organizations.models import CompanyMembership, CompanyRole
from apps.platform_core.errors import PlatformPermissionException
from apps.platform_core.mixins import TenantAPIView

from ..serializers import (
    PilotChangeRequestListSerializer,
    PilotChangeRequestCreateSerializer,
    PilotChangeRequestSerializer,
    PilotChangeRequestUpdateSerializer,
    PilotCharterCreateSerializer,
    PilotCharterSerializer,
    PilotDashboardSerializer,
    PilotIssueListSerializer,
    PilotIssueCreateSerializer,
    PilotIssueSerializer,
    PilotIssueUpdateSerializer,
    PilotProgramSerializer,
    PilotProgramUpdateSerializer,
    PilotWeeklyReportListSerializer,
    PilotWeeklyReportCreateSerializer,
    PilotWeeklyReportSerializer,
)
from ..services import (
    create_change_request,
    create_issue,
    create_weekly_report,
    decide_change_request,
    latest_charter,
    pilot_dashboard,
    pilot_program_for_company,
    resolve_issue,
    sign_charter,
    update_program,
)



def _owner_or_monitor(company, user):
    membership = CompanyMembership.objects.filter(company=company, user=user, active=True).only("role").first()
    if membership is None or membership.role not in {CompanyRole.OWNER, CompanyRole.MONITOR}:
        raise PlatformPermissionException("Owner or monitor access required.")


class PilotProgramView(TenantAPIView):
    # BE-01: Pilot program is OWNER + MONITOR (matches the existing
    # ``_owner_or_monitor`` gate on the PATCH path).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=PilotProgramSerializer)
    def get(self, request):
        company = self.get_tenant().company
        return Response(PilotProgramSerializer(pilot_program_for_company(company)).data)

    @extend_schema(request=PilotProgramUpdateSerializer, responses=PilotProgramSerializer)
    def patch(self, request):
        company = self.get_tenant().company
        _owner_or_monitor(company, request.user)
        serializer = PilotProgramUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        program = update_program(company, request.user, serializer.validated_data)
        return Response(PilotProgramSerializer(program).data)


class PilotDashboardView(TenantAPIView):
    # BE-01: Pilot dashboard is OWNER + MONITOR (matches existing helper).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=PilotDashboardSerializer)
    def get(self, request):
        company = self.get_tenant().company
        _owner_or_monitor(company, request.user)
        return Response(pilot_dashboard(company, request.user))


class PilotWeeklyReportView(TenantAPIView):
    # BE-01: Weekly reports are OWNER + MONITOR (matches existing helper).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=PilotWeeklyReportListSerializer)
    def get(self, request):
        company = self.get_tenant().company
        program = pilot_program_for_company(company)
        return Response({"reports": PilotWeeklyReportSerializer(program.weekly_reports.order_by("-week_ending"), many=True).data})

    @extend_schema(request=PilotWeeklyReportCreateSerializer, responses={201: PilotWeeklyReportSerializer})
    def post(self, request):
        company = self.get_tenant().company
        _owner_or_monitor(company, request.user)
        serializer = PilotWeeklyReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = create_weekly_report(company, request.user, serializer.validated_data)
        return Response(PilotWeeklyReportSerializer(report).data, status=201)


class PilotIssueView(TenantAPIView):
    # BE-01: Pilot issues are OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=PilotIssueListSerializer)
    def get(self, request):
        company = self.get_tenant().company
        program = pilot_program_for_company(company)
        return Response({"issues": PilotIssueSerializer(program.issues.order_by("-created_at"), many=True).data})

    @extend_schema(request=PilotIssueCreateSerializer, responses={201: PilotIssueSerializer})
    def post(self, request):
        company = self.get_tenant().company
        _owner_or_monitor(company, request.user)
        serializer = PilotIssueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue = create_issue(company, request.user, serializer.validated_data)
        return Response(PilotIssueSerializer(issue).data, status=201)


class PilotChangeRequestView(TenantAPIView):
    # BE-01: Pilot change requests are OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=PilotChangeRequestListSerializer)
    def get(self, request):
        company = self.get_tenant().company
        program = pilot_program_for_company(company)
        return Response({"change_requests": PilotChangeRequestSerializer(program.change_requests.order_by("-created_at"), many=True).data})

    @extend_schema(request=PilotChangeRequestCreateSerializer, responses={201: PilotChangeRequestSerializer})
    def post(self, request):
        company = self.get_tenant().company
        _owner_or_monitor(company, request.user)
        serializer = PilotChangeRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change = create_change_request(company, request.user, serializer.validated_data)
        return Response(PilotChangeRequestSerializer(change).data, status=201)


class PilotIssueDetailView(TenantAPIView):
    # BE-01: Resolving a pilot issue is OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=PilotIssueUpdateSerializer, responses=PilotIssueSerializer)
    def patch(self, request, issue_id):
        company = self.get_tenant().company
        _owner_or_monitor(company, request.user)
        serializer = PilotIssueUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue = resolve_issue(company, request.user, issue_id, serializer.validated_data)
        return Response(PilotIssueSerializer(issue).data)


class PilotChangeRequestDetailView(TenantAPIView):
    # BE-01: Deciding a pilot change request is OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=PilotChangeRequestUpdateSerializer, responses=PilotChangeRequestSerializer)
    def patch(self, request, change_id):
        company = self.get_tenant().company
        _owner_or_monitor(company, request.user)
        serializer = PilotChangeRequestUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change = decide_change_request(company, request.user, change_id, serializer.validated_data)
        return Response(PilotChangeRequestSerializer(change).data)


class PilotCharterView(TenantAPIView):
    """PILOT-01: read or sign the pilot charter.

    - ``GET`` returns the most recent signed charter (404 if none).
    - ``POST`` signs a new charter; only OWNERs may sign. The charter is
      HMAC-signed over the canonical payload and the audit event
      ``PILOT_CHARTER_SIGNED`` is recorded.
    """

    # BE-01: reading the charter is OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=PilotCharterSerializer)
    def get(self, request):
        company = self.get_tenant().company
        charter = latest_charter(company)
        if charter is None:
            return Response({"error": {"code": "PILOT-CHARTER-001", "message": "No charter has been signed yet."}}, status=404)
        return Response(PilotCharterSerializer(charter).data)

    @extend_schema(request=PilotCharterCreateSerializer, responses={201: PilotCharterSerializer})
    def post(self, request):
        company = self.get_tenant().company
        # PILOT-01: only the platform owner signs the charter.
        membership = CompanyMembership.objects.filter(company=company, user=request.user, active=True).only("role").first()
        if membership is None or membership.role != CompanyRole.OWNER:
            raise PlatformPermissionException("Only the company owner can sign the pilot charter.")
        serializer = PilotCharterCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.audit.services import record_audit_event
        charter = sign_charter(company, request.user, serializer.validated_data)
        record_audit_event(
            event_type="PILOT_CHARTER_SIGNED",
            target_type="pilot_charter",
            target_id=str(charter.id),
            actor_id=str(request.user.id),
            branch_id="",
            metadata={
                "pilot_program_id": str(charter.pilot_program_id),
                "decision": charter.decision,
            },
        )
        return Response(PilotCharterSerializer(charter).data, status=201)
