"""Compliance REST API views.

The compliance surface is split into three resource groups:

* ``/api/v1/compliance/ropa`` — read-only list of published ROPA
  rows. The list is the publicly published ROPA; the underlying rows
  are managed through the platform-side management command.
* ``/api/v1/compliance/dsr`` — Data Subject Rights intake and
  workflow. The list endpoint is tenant-scoped; the transition
  endpoint is owner-only and audited.
* ``/api/v1/compliance/legal-documents`` — read-only list of the
  currently published legal documents, so the UI can fetch the
  active versions.

The intake endpoint is unauthenticated by design; the public DSR
form posts here, the audit log captures the submitter.
"""

from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.platform_core.errors import PlatformAPIException, platform_service_call
from apps.platform_core.mixins import TenantAPIView

from ..models import DSRRequest, LegalDocument
from ..serializers import (
    DSRDecisionSerializer,
    DSRRejectionSerializer,
    DSRRequestCreateSerializer,
    DSRRequestSerializer,
    LegalDocumentSerializer,
    ProcessingActivitySerializer,
)
from ..services import (
    complete_dsr_request,
    list_published_activities,
    reject_dsr_request,
    start_dsr_work,
    submit_dsr_request,
    verify_dsr_identity,
)
from apps.organizations.models import CompanyRole


class ProcessingActivityListView(APIView):
    """Public, read-only list of published ROPA rows."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: ProcessingActivitySerializer(many=True)})
    def get(self, request):
        activities = list_published_activities()
        return Response({"activities": ProcessingActivitySerializer(activities, many=True).data})


class DSRRequestListView(TenantAPIView):
    """Tenant-scoped Data Subject Rights request list and intake.

    * ``GET`` — list DSR requests for the active company (owner/monitor
      only). Useful for the company's privacy inbox.
    * ``POST`` — submit a new DSR request. Available to any
      authenticated user in the active tenant; the public DSR form
      uses an unauthenticated path that bypasses ``TenantAPIView``.
    """

    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses={200: DSRRequestSerializer(many=True)})
    def get(self, request):
        company = self.get_tenant().company
        requests = DSRRequest.objects.filter(company=company).order_by("-submitted_at")
        return Response({"requests": DSRRequestSerializer(requests, many=True).data})

    @extend_schema(request=DSRRequestCreateSerializer, responses={201: DSRRequestSerializer})
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        serializer = DSRRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dsr = submit_dsr_request(
            company=company,
            request_type=serializer.validated_data["request_type"],
            subject_email=serializer.validated_data["subject_email"],
            subject_reference=serializer.validated_data.get("subject_reference", ""),
            description=serializer.validated_data.get("description", ""),
            submitted_by=request.user,
        )
        return Response(DSRRequestSerializer(dsr).data, status=status.HTTP_201_CREATED)


class DSRRequestTransitionView(APIView):
    """State-machine transitions for a single :class:`DSRRequest`.

    The view is dispatched through ``as_view(action="...")`` in the URL
    config; the ``action`` kwarg becomes a class attribute on the
    view instance and the request handler reads it from ``self``.

    * ``POST /api/v1/compliance/dsr/<id>/verify`` — identity verified
    * ``POST /api/v1/compliance/dsr/<id>/start`` — work in progress
    * ``POST /api/v1/compliance/dsr/<id>/complete`` — completed
    * ``POST /api/v1/compliance/dsr/<id>/reject`` — rejected with reason

    All endpoints require an authenticated owner; the DPO can be
    wired through ``apps.identity`` when the platform user role is
    extended.
    """

    permission_classes = [IsAuthenticated]
    action: str = ""

    def _get_request(self, pk: str) -> DSRRequest:
        try:
            return DSRRequest.objects.select_related("company").get(id=pk)
        except DSRRequest.DoesNotExist as exc:
            raise PlatformAPIException("DSR request not found.") from exc

    def _require_owner(self, request, dsr: DSRRequest) -> None:
        company = dsr.company
        from apps.tenancy.services import is_owner  # local import to avoid cycle
        if not is_owner(request.user, company):
            raise PlatformAPIException("Only the company owner can decide DSR requests.")

    @extend_schema(request=DSRDecisionSerializer, responses=DSRRequestSerializer)
    def post(self, request, pk: str):
        dsr = self._get_request(pk)
        self._require_owner(request, dsr)
        actor_id = str(request.user.id)
        action = self.action
        if action == "verify":
            verify_dsr_identity(dsr, actor_id=actor_id)
        elif action == "start":
            start_dsr_work(dsr, actor_id=actor_id)
        elif action == "complete":
            complete_dsr_request(dsr, actor_id=actor_id, decided_by=request.user)
        elif action == "reject":
            serializer = DSRRejectionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            reject_dsr_request(
                dsr,
                actor_id=actor_id,
                decided_by=request.user,
                reason=serializer.validated_data["reason"],
            )
        else:
            raise PlatformAPIException(f"Unknown DSR action: {action!r}.")
        dsr.refresh_from_db()
        return Response(DSRRequestSerializer(dsr).data)


class LegalDocumentListView(APIView):
    """Read-only list of currently published legal documents."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: LegalDocumentSerializer(many=True)})
    def get(self, request):
        documents: QuerySet[LegalDocument] = LegalDocument.objects.filter(is_current=True).order_by("kind")
        return Response({"documents": LegalDocumentSerializer(documents, many=True).data})
