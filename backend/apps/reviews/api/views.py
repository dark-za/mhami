from __future__ import annotations

from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.organizations.models import CompanyRole
from apps.audit.services import record_audit_event
from apps.evidence.models import EvidenceItem, TaskIssueReport
from apps.platform_core.errors import platform_service_call, PlatformAPIException
from apps.platform_core.mixins import TenantAPIView
from apps.tasks.models import TaskInstance
from apps.tenancy.access import validate_company_reference_or_none

from ..serializers import ReviewDecisionCreateSerializer, ReviewDecisionSerializer, ReviewPolicySerializer, ReviewPolicyUpdateSerializer
from ..services import create_review_decision, dashboard_summary, policy_for_company, review_queue



class ReviewDashboardView(TenantAPIView):
    # BE-01: Review dashboard is a management view; OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="Review dashboard summary."))

    @platform_service_call
    def get(self, request):
        company = self.get_tenant().company
        return Response(dashboard_summary(company, request.user))


class ReviewQueueView(TenantAPIView):
    # BE-01: Review queue is a management view; OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="Review queue items."))

    @platform_service_call
    def get(self, request):
        company = self.get_tenant().company
        return Response({"items": review_queue(company, request.user)})


class ReviewPolicyView(TenantAPIView):
    # H-02: all company roles may read the review policy; only OWNERs mutate it.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=ReviewPolicySerializer)

    @platform_service_call
    def get(self, request):
        company = self.get_tenant().company
        return Response(ReviewPolicySerializer(policy_for_company(company)).data)

    @extend_schema(request=ReviewPolicyUpdateSerializer, responses=ReviewPolicySerializer)

    @platform_service_call
    def patch(self, request):
        context = self.get_tenant()
        context.require_roles(str(CompanyRole.OWNER))
        company = context.company
        policy = policy_for_company(company)
        serializer = ReviewPolicyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(policy, field, value)
        policy.updated_by = request.user
        policy.save()
        record_audit_event(
            event_type="REVIEW_POLICY_UPDATED",
            target_type="review_policy_setting",
            target_id=str(policy.id),
            actor_id=str(request.user.id),
            branch_id="",
            metadata=dict(serializer.validated_data),
        )
        return Response(ReviewPolicySerializer(policy).data)


class ReviewDecisionCreateView(TenantAPIView):
    # H-01: only OWNERs and MONITORs may record review decisions. The
    # class-level check is the single source of truth so the role gate is
    # applied uniformly across all decision sub-routes.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=ReviewDecisionCreateSerializer, responses={201: ReviewDecisionSerializer})

    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        serializer = ReviewDecisionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # BE-02: every external ID must be re-checked against the active
        # company. ``validate_company_reference_or_none`` raises
        # ``PlatformPermissionException`` (mapped to 403) if the record
        # belongs to another tenant, mirroring the historical in-method
        # checks and closing the IDOR surface even when the serializer
        # field type allows arbitrary UUIDs.
        validate_company_reference_or_none(
            company,
            TaskInstance,
            serializer.validated_data.get("task_instance_id"),
        )
        validate_company_reference_or_none(
            company,
            EvidenceItem,
            serializer.validated_data.get("evidence_item_id"),
        )
        validate_company_reference_or_none(
            company,
            TaskIssueReport,
            serializer.validated_data.get("issue_report_id"),
        )
        try:
            decision = create_review_decision(
            company=company,
            user=request.user,
            decision_type=serializer.validated_data["decision_type"],
            reason=serializer.validated_data.get("reason", ""),
            task_instance_id=str(serializer.validated_data.get("task_instance_id")) if serializer.validated_data.get("task_instance_id") else None,
            evidence_item_id=str(serializer.validated_data.get("evidence_item_id")) if serializer.validated_data.get("evidence_item_id") else None,
            issue_report_id=str(serializer.validated_data.get("issue_report_id")) if serializer.validated_data.get("issue_report_id") else None,
            restriction_name=serializer.validated_data.get("restriction_name", ""),
        )
        except ValueError as exc:
            raise PlatformAPIException(str(exc)) from exc
        return Response(ReviewDecisionSerializer(decision).data, status=201)
