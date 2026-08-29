from __future__ import annotations

from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.organizations.models import CompanyRole
from apps.platform_core.errors import PlatformAPIException
from apps.platform_core.mixins import TenantAPIView
from apps.tenancy.access import has_company_role, validate_company_reference, validate_company_reference_or_none

from ..models import AIAnalysisCriterion
from ..serializers import (
    AIAnalysisCriterionCreateSerializer,
    AIAnalysisCriterionSerializer,
    AIAnalysisRunCreateSerializer,
    AIAnalysisRunSerializer,
    AIProviderConfigSerializer,
    AIProviderConfigUpdateSerializer,
)
from ..services import create_criterion, provider_config_for_company, run_analysis, shadow_summary, upsert_provider_config, criteria_summary



def _owner_or_400(company, user):
    if not has_company_role(company, user, str(CompanyRole.OWNER)):
        raise PlatformAPIException("Owner access required.")


class ProviderConfigView(TenantAPIView):
    # BE-01: Read is restricted to OWNER + MONITOR (matches the historical
    # ``_owner_or_400`` gate used for the PATCH path). Class-level
    # enforcement ensures the read endpoint cannot accidentally leak
    # provider credentials to an employee in the future.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=AIProviderConfigSerializer)
    def get(self, request):
        company = self.get_tenant().company
        return Response(AIProviderConfigSerializer(provider_config_for_company(company)).data)

    @extend_schema(request=AIProviderConfigUpdateSerializer, responses=AIProviderConfigSerializer)
    def patch(self, request):
        # The class-level role check already restricts the endpoint to
        # OWNER/MONITOR. The legacy ``_owner_or_400`` helper is preserved
        # to fail fast at the start of the method body for any future
        # relaxation of the class-level contract.
        company = self.get_tenant().company
        _owner_or_400(company, request.user)
        serializer = AIProviderConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = upsert_provider_config(company, request.user, serializer.validated_data)
        return Response(AIProviderConfigSerializer(config).data)


class CriteriaView(TenantAPIView):
    # BE-01: AI criteria are management tooling; restrict to OWNER + MONITOR
    # which mirrors the existing in-method role check.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="Company AI analysis criteria summary."))
    def get(self, request):
        company = self.get_tenant().company
        return Response({"criteria": criteria_summary(company)})

    @extend_schema(request=AIAnalysisCriterionCreateSerializer, responses={201: AIAnalysisCriterionSerializer})
    def post(self, request):
        company = self.get_tenant().company
        if not has_company_role(company, request.user, str(CompanyRole.OWNER), str(CompanyRole.MONITOR)):
            raise PlatformAPIException("Monitor or owner access required.")
        serializer = AIAnalysisCriterionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        criterion = create_criterion(company, request.user, serializer.validated_data)
        return Response(AIAnalysisCriterionSerializer(criterion).data, status=201)


class AnalysisRunView(TenantAPIView):
    # BE-01: AI analysis is triggered by any company user that can submit
    # evidence. Open to all tenant roles; the per-evidence scoping inside
    # the service layer prevents cross-tenant data exposure.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=AIAnalysisRunCreateSerializer, responses={201: AIAnalysisRunSerializer})
    def post(self, request):
        company = self.get_tenant().company
        serializer = AIAnalysisRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # BE-02: validate the evidence and criterion references against
        # the active company. ``EvidenceItem`` is imported inside the
        # service to keep the API module's import surface small, but
        # ``AIAnalysisCriterion`` lives in this app.
        from apps.evidence.models import EvidenceItem

        validate_company_reference(
            company, EvidenceItem, serializer.validated_data["evidence_item_id"]
        )
        validate_company_reference_or_none(
            company, AIAnalysisCriterion, serializer.validated_data.get("criterion_id")
        )
        run = run_analysis(
            company,
            request.user,
            str(serializer.validated_data["evidence_item_id"]),
            str(serializer.validated_data.get("criterion_id")) if serializer.validated_data.get("criterion_id") else None,
        )
        return Response(AIAnalysisRunSerializer(run).data, status=201)


class ShadowSummaryView(TenantAPIView):
    # BE-01: Shadow-mode agreement is a management view; restrict to
    # OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="AI shadow-mode agreement and error summary."))
    def get(self, request):
        company = self.get_tenant().company
        return Response(shadow_summary(company, request.user))
