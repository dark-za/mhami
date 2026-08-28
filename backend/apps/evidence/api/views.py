from __future__ import annotations

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.platform_core.errors import PlatformAPIException, platform_service_call
from apps.platform_core.mixins import TenantAPIView
from apps.organizations.models import CompanyRole
from apps.tasks.models import TaskInstance
from apps.tenancy.access import validate_company_reference, validate_company_reference_or_none

from ..models import CaptureSession, EvidenceItem, TaskDiscussionMessage, TaskIssueReport
from ..serializers import (
    CaptureSessionCreateSerializer,
    CaptureSessionSerializer,
    EvidenceItemSerializer,
    EvidenceSubmitSerializer,
    TaskDiscussionCreateSerializer,
    TaskDiscussionMessageSerializer,
    TaskIssueCreateSerializer,
    TaskIssueReportSerializer,
)
from ..services import (
    can_access_media,
    create_capture_session,
    create_discussion_message,
    create_issue_report,
    media_file_response,
    submit_evidence,
)


class CaptureSessionView(TenantAPIView):
    # BE-01: Capture sessions are created by the user that owns the task
    # instance; open to all tenant roles. The per-task scoping happens in
    # the body of the handler.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=CaptureSessionCreateSerializer, responses={201: CaptureSessionSerializer})
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        serializer = CaptureSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # BE-02: validate the task reference explicitly. We keep the
        # ``.get(..., company=company)`` style here for backwards
        # compatibility with the test contract, but the explicit
        # ``validate_company_reference`` call below closes the IDOR
        # surface that ``get_or_404`` would otherwise mask behind a 404.
        task_instance = validate_company_reference(
            company, TaskInstance, serializer.validated_data["task_instance_id"]
        )
        session = create_capture_session(
            task_instance=task_instance,
            user=request.user,
            evidence_type=serializer.validated_data["evidence_type"],
            challenge_answer=serializer.validated_data.get("challenge_answer", ""),
        )
        return Response(CaptureSessionSerializer(session).data, status=201)


class EvidenceSubmitView(TenantAPIView):
    # BE-01: Submitting evidence is a tenant-wide capability. The
    # per-session scoping inside the body of the handler enforces
    # ownership.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(request=EvidenceSubmitSerializer, responses={201: EvidenceItemSerializer})
    @platform_service_call
    def post(self, request):
        self.get_tenant()
        serializer = EvidenceSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = submit_evidence(
            session_token=serializer.validated_data["capture_token"],
            user=request.user,
            upload=request.FILES.get("file"),
            note_text=serializer.validated_data.get("note_text", ""),
            number_value=serializer.validated_data.get("number_value"),
            confirmation_value=serializer.validated_data.get("confirmation_value"),
            face_detected=serializer.validated_data.get("face_detected", False),
            challenge_response=serializer.validated_data.get("challenge_response", ""),
        )
        return Response(EvidenceItemSerializer(item).data, status=201)


class EvidenceTaskView(TenantAPIView):
    # BE-01: Evidence, issues, messages, and capture sessions for a task
    # are scoped to the company already via ``for_company(company)`` and the
    # task lookup. The role gate is added here to align with the platform's
    # single source of truth for tenant RBAC and prevent any future code
    # path that bypasses the scoping helpers from leaking data to the
    # wrong role.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="Evidence, issues, messages, and capture sessions for a task instance."))
    def get(self, request, task_instance_id):
        context = self.get_tenant()
        company = context.company
        # BE-02: validate the task reference against the active company.
        task = validate_company_reference(company, TaskInstance, task_instance_id)
        # C-07: branch scope check. A user with branch-level access can
        # only see workflows for branches in their active scope.
        context.require_branch(task.branch_id)
        evidence = EvidenceItem.objects.for_company(company).filter(task_instance=task).order_by("sequence_number")
        issues = TaskIssueReport.objects.for_company(company).filter(task_instance=task).order_by("created_at")
        messages = TaskDiscussionMessage.objects.for_company(company).filter(task_instance=task).order_by("created_at")
        sessions = CaptureSession.objects.for_company(company).filter(task_instance=task).order_by("created_at")
        return Response(
            {
                "task_instance_id": str(task.id),
                "evidence": EvidenceItemSerializer(evidence, many=True).data,
                "issues": TaskIssueReportSerializer(issues, many=True).data,
                "messages": TaskDiscussionMessageSerializer(messages, many=True).data,
                "capture_sessions": CaptureSessionSerializer(sessions, many=True).data,
            }
        )


class EvidenceMediaView(TenantAPIView):
    # BE-01: Private media downloads are gated to the same set of roles
    # that can author or review evidence inside the active company.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="Private media file for an evidence item."))
    def get(self, request, evidence_id):
        context = self.get_tenant()
        company = context.company
        evidence = EvidenceItem.objects.select_related("branch", "company", "submitted_by").get(id=evidence_id, company=company)
        # C-07: branch scope is enforced before media access.
        context.require_branch(evidence.branch_id)
        if not can_access_media(request.user, evidence):
            raise PlatformAPIException("Media access denied.")
        return media_file_response(evidence)


class IssueCreateView(TenantAPIView):
    # BE-01: Filing an issue is a tenant-wide capability.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=TaskIssueCreateSerializer, responses={201: TaskIssueReportSerializer})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        company = context.company
        serializer = TaskIssueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # BE-02: validate the task reference against the active company.
        task = validate_company_reference(
            company, TaskInstance, serializer.validated_data["task_instance_id"]
        )
        # C-07: branch scope check.
        context.require_branch(task.branch_id)
        issue = create_issue_report(task, request.user, serializer.validated_data["note"], request.FILES.get("file"))
        return Response(TaskIssueReportSerializer(issue).data, status=201)


class IssueMessagesView(TenantAPIView):
    # BE-01: Discussion messages on an issue are visible to any role that
    # can author evidence in the active company. The check is centralised
    # here so the message thread is consistently gated.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="Discussion messages for an issue."))
    def get(self, request, issue_id):
        context = self.get_tenant()
        company = context.company
        issue = TaskIssueReport.objects.get(id=issue_id, company=company)
        # C-07: branch scope check.
        context.require_branch(issue.branch_id)
        messages = TaskDiscussionMessage.objects.filter(issue_report=issue).order_by("created_at")
        return Response({"messages": TaskDiscussionMessageSerializer(messages, many=True).data})

    @extend_schema(request=TaskDiscussionCreateSerializer, responses={201: TaskDiscussionMessageSerializer})
    @platform_service_call
    def post(self, request, issue_id):
        context = self.get_tenant()
        company = context.company
        serializer = TaskDiscussionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # BE-02: validate every external ID against the active company.
        issue = validate_company_reference(company, TaskIssueReport, issue_id)
        # C-07: branch scope check on the issue first.
        context.require_branch(issue.branch_id)
        task = validate_company_reference(
            company, TaskInstance, serializer.validated_data["task_instance_id"]
        )
        # Then verify the supplied task and issue are in the same branch.
        if task.branch_id != issue.branch_id:
            raise PlatformAPIException("Issue and task must belong to the same branch.")
        context.require_branch(task.branch_id)
        reply_to = validate_company_reference_or_none(
            company,
            TaskDiscussionMessage,
            serializer.validated_data.get("reply_to_id"),
        )
        if reply_to is not None and reply_to.branch_id != issue.branch_id:
            raise PlatformAPIException("Reply target is outside the issue branch.")
        message = create_discussion_message(task, request.user, serializer.validated_data["message"], issue_report=issue, reply_to=reply_to)
        return Response(TaskDiscussionMessageSerializer(message).data, status=201)


class MediaHealthView(TenantAPIView):
    # Public health endpoint; explicitly override the inherited auth/role
    # checks so it can be hit by the monitoring stack.
    permission_classes = []
    required_roles = ()

    @extend_schema(responses=OpenApiResponse(description="Media subsystem health."))
    def get(self, request):
        return Response({"status": "ok", "queue": "media", "storage": "private"})
