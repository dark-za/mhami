from __future__ import annotations

from django.http import FileResponse
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.organizations.models import CompanyRole
from apps.platform_core.errors import PlatformAPIException, platform_service_call
from apps.platform_core.mixins import TenantAPIView

from apps.tenancy.access import validate_company_reference
from apps.tenancy.services import ensure_company_operational

from ..models import BackupRun
from ..serializers import (
    BackupCreateSerializer,
    BackupPolicySerializer,
    BackupRunSerializer,
    RestoreCreateSerializer,
    RestoreRunSerializer,
)
from ..services import (
    backup_policy_for_company,
    create_backup_run,
    download_backup_artifact,
    restore_backup_run,
)


class BackupPolicyView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="Backup policy for the active company."))
    def get(self, request):
        company = self.get_tenant().company
        return Response(BackupPolicySerializer(backup_policy_for_company(company)).data)

    @extend_schema(request=BackupCreateSerializer, responses=BackupPolicySerializer)
    @platform_service_call
    def put(self, request):
        company = self.get_tenant().company
        ensure_company_operational(company)
        serializer = BackupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Policy updates are read-only in the current implementation.
        return Response(BackupPolicySerializer(backup_policy_for_company(company)).data)


class BackupRunListView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="List of backup runs for the active company."))
    def get(self, request):
        company = self.get_tenant().company
        return Response(
            {
                "runs": BackupRunSerializer(
                    BackupRun.objects.filter(company=company).order_by("-created_at"),
                    many=True,
                ).data,
            }
        )


class BackupRunView(TenantAPIView):
    # H-07: OWNER-only for backup creation; MONITOR is read-only.
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(request=BackupCreateSerializer, responses={201: BackupRunSerializer})
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        ensure_company_operational(company)
        serializer = BackupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        run = create_backup_run(
            company=company,
            user=request.user,
            include_private_media=validated.get("include_private_media", True),
            include_configuration=validated.get("include_configuration", True),
            include_tenant_state=validated.get("include_tenant_state", True),
        )
        return Response(BackupRunSerializer(run).data, status=201)


class BackupRestoreView(TenantAPIView):
    # H-07: restore is a destructive action and remains OWNER-only.
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(request=RestoreCreateSerializer, responses=RestoreRunSerializer)
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        ensure_company_operational(company)
        serializer = RestoreCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        # BE-02: validate the backup reference against the active
        # company so an OWNER cannot restore a backup run that belongs to
        # another tenant by replaying its UUID.
        validate_company_reference(company, BackupRun, validated["backup_run_id"])
        try:
            run = restore_backup_run(
                company=company,
                user=request.user,
                backup_run_id=str(validated["backup_run_id"]),
                target_name=validated["target_name"],
                confirmation=validated["confirmation"],
            )
        except ValueError as exc:
            raise PlatformAPIException(str(exc)) from exc
        return Response(RestoreRunSerializer(run).data, status=201)


class BackupDownloadView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses={200: OpenApiResponse(description="Backup archive download.")})
    def get(self, request, backup_run_id):
        company = self.get_tenant().company
        path = download_backup_artifact(company, backup_run_id)
        if path is None:
            raise PlatformAPIException("Backup archive is unavailable.")
        return FileResponse(open(path, "rb"), as_attachment=True, filename=path.name)
