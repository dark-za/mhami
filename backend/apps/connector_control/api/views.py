from __future__ import annotations

from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.organizations.models import CompanyMembership, CompanyRole
from apps.platform_core.errors import platform_service_call, PlatformAPIException, PlatformPermissionException
from apps.platform_core.mixins import TenantAPIView

from ..models import TenantConnectorEnrollment
from ..serializers import (
    ConnectorHeartbeatSerializer,
    TenantConnectorEnrollSerializer,
    TenantConnectorEnrollmentSerializer,
    TenantConnectorRevokeSerializer,
)
from ..services import current_connector_health, enroll_connector, observe_connector_health, revoke_connector



def _owner_or_400(company, user):
    membership = CompanyMembership.objects.filter(company=company, user=user, active=True).only("role").first()
    if membership is None or membership.role != CompanyRole.OWNER:
        raise PlatformAPIException("Owner access required.")


class ConnectorEnrollmentView(TenantAPIView):
    # BE-01: Connector enrollment is a management surface. OWNER + MONITOR
    # can read; the in-method ``_owner_or_400`` keeps the POST as
    # OWNER-only.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="Current tenant connector enrollment."))

    @platform_service_call
    def get(self, request):
        company = self.get_tenant().company
        enrollment = TenantConnectorEnrollment.objects.filter(company=company).first()
        if enrollment is None:
            return Response({"enrollment": None})
        enrollment = current_connector_health(enrollment)
        return Response({"enrollment": TenantConnectorEnrollmentSerializer(enrollment).data})

    @extend_schema(request=TenantConnectorEnrollSerializer, responses={201: TenantConnectorEnrollmentSerializer})

    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        _owner_or_400(company, request.user)
        serializer = TenantConnectorEnrollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = enroll_connector(
            company,
            request.user,
            serializer.validated_data["connector_version"],
            serializer.validated_data["shared_secret_fingerprint"],
            serializer.validated_data.get("health_ttl_seconds", 300),
        )
        return Response(TenantConnectorEnrollmentSerializer(enrollment).data, status=201)


class ConnectorHealthView(TenantAPIView):
    # BE-01: Health is a management view (mirrors ``ConnectorEnrollmentView``).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="Tenant connector health status."))

    @platform_service_call
    def get(self, request):
        company = self.get_tenant().company
        enrollment = TenantConnectorEnrollment.objects.filter(company=company).first()
        if enrollment is None:
            return Response({"status": "offline", "enrollment": None})
        enrollment = current_connector_health(enrollment)
        return Response({"status": enrollment.health_status, "enrollment": TenantConnectorEnrollmentSerializer(enrollment).data})


class ConnectorHeartbeatView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(request=ConnectorHeartbeatSerializer, responses=TenantConnectorEnrollmentSerializer)

    @platform_service_call
    def post(self, request):
        serializer = ConnectorHeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        secret = request.headers.get("X-Connector-Secret", "")
        if not secret:
            raise PlatformPermissionException("Invalid connector credentials.")
        try:
            enrollment = observe_connector_health(
                str(serializer.validated_data["enrollment_id"]),
                serializer.validated_data["connector_version"],
                secret,
                serializer.validated_data["provider_status"],
            )
        except PermissionError as exc:
            raise PlatformPermissionException("Invalid connector credentials.") from exc
        return Response(TenantConnectorEnrollmentSerializer(enrollment).data)


class ConnectorRevokeView(TenantAPIView):
    # BE-01: Revocation is a destructive management action; OWNER only,
    # matching the existing ``_owner_or_400`` helper.
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(request=TenantConnectorRevokeSerializer, responses=TenantConnectorEnrollmentSerializer)

    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        _owner_or_400(company, request.user)
        serializer = TenantConnectorRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = revoke_connector(company, request.user, serializer.validated_data.get("reason", ""))
        return Response(TenantConnectorEnrollmentSerializer(enrollment).data)
