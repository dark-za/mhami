from __future__ import annotations

from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.organizations.models import CompanyRole
from apps.platform_core.errors import PlatformAPIException, platform_service_call
from apps.platform_core.mixins import TenantAPIView

from apps.tenancy.services import ensure_company_operational

from ..models import ExportRequest
from ..serializers import (
    ExportBoundaryPolicySerializer,
    ExportRequestCreateSerializer,
    ExportRequestListSerializer,
    ExportRequestSerializer,
)
from ..services import complete_export_request, export_download_response, prepare_export_request


class ExportPolicyView(TenantAPIView):
    # BE-01: Export policy is a management view; OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=ExportBoundaryPolicySerializer)
    def get(self, request):
        return Response(ExportBoundaryPolicySerializer({}).data)


class ExportRequestListView(TenantAPIView):
    # BE-01: Listing export requests is a management view; OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=ExportRequestListSerializer)
    def get(self, request):
        company = self.get_tenant().company
        return Response(
            {
                "exports": ExportRequestSerializer(
                    ExportRequest.objects.filter(company=company).order_by("-created_at"),
                    many=True,
                ).data,
            }
        )


class ExportRequestView(TenantAPIView):
    # H-07: OWNERs can export any branch, MONITORs can export only the
    # branches in their active scope. The branch-scope check below is
    # the service-layer enforcement that matches the test contract.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=ExportRequestCreateSerializer, responses={201: ExportRequestSerializer})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        company = context.company
        ensure_company_operational(company)
        serializer = ExportRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        try:
            export = prepare_export_request(
                company=company,
                user=request.user,
                export_type=validated["export_type"],
                branch_ids=[str(branch_id) for branch_id in validated.get("branch_ids", [])],
                categories=list(validated.get("categories", [])),
                start_date=validated.get("start_date"),
                end_date=validated.get("end_date"),
            )
            export = complete_export_request(str(export.id))
        except ValueError as exc:
            raise PlatformAPIException(str(exc)) from exc
        return Response(ExportRequestSerializer(export).data, status=201)


class ExportDownloadView(TenantAPIView):
    # BE-01: Downloading export artefacts is a management view; OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses={200: OpenApiResponse(description="Export artifact stream.")})
    def get(self, request, token):
        company = self.get_tenant().company
        return export_download_response(company, request.user, token)
