from __future__ import annotations

from typing import Any

from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.audit.services import record_audit_event
from apps.platform_core.api.serializers import (
    BootstrapSerializer,
    ExitDecisionCreateSerializer,
    ExitDecisionSerializer,
)
from apps.platform_core.health import live_status, ready_status
from apps.platform_core.metrics import metrics_response
from apps.platform_core.models import ExitDecision
from apps.platform_core.services import bootstrap_payload, metrics_report, module_health_report


class LiveHealthView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes: list[type[Any]] = []

    @extend_schema(exclude=True)
    def get(self, request):
        return Response(live_status())


class ReadyHealthView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes: list[type[Any]] = []

    @extend_schema(exclude=True)
    def get(self, request):
        return Response(ready_status())


class ModulesHealthView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes: list[type[Any]] = []

    @extend_schema(exclude=True)
    def get(self, request):
        return Response({"modules": module_health_report()})


class SystemStatusView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(exclude=True)
    def get(self, request):
        return Response({"status": "ok", "modules": module_health_report(), "metrics": metrics_report()})


@extend_schema(exclude=True)
def metrics_view(request):
    return metrics_response(request)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class BootstrapView(APIView):
    # C-04: bootstrap is the documented entry point for clients to obtain
    # a csrftoken cookie. It must be reachable without authentication and
    # without an existing CSRF token, so both gates are disabled.
    authentication_classes: list[type[Any]] = []
    permission_classes: list[type[Any]] = []

    @extend_schema(responses=BootstrapSerializer)
    def get(self, request):
        return Response(bootstrap_payload(request.user))


class ExitDecisionView(APIView):
    """C-06: sign a phase exit decision. Restricted to platform administrators."""

    permission_classes = [IsAuthenticated]
    # The decorator enables CSRF cookie issuance so browser clients can
    # attach the token to the POST without a separate bootstrap hop.
    @method_decorator(ensure_csrf_cookie)
    def post(self, request, phase: str):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": {"code": "CORE-FORBIDDEN-001", "message": "Only platform administrators can sign exit decisions."}},
                status=403,
            )
        serializer = ExitDecisionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # PILOT-01: phase12 decisions must reference a PilotProgram that has
        # at least one signed authorize-charter. This is the system-level
        # guard that turns the markdown template into verifiable evidence.
        metadata = dict(serializer.validated_data.get("metadata") or {})
        if phase == "phase12":
            pilot_program_id = metadata.get("pilot_program_id")
            if not pilot_program_id:
                return Response(
                    {"error": {"code": "PILOT-CHARTER-002", "message": "metadata.pilot_program_id is required for phase12 exit decisions."}},
                    status=400,
                )
            from apps.pilot.models import PilotCharter, PilotProgram
            from apps.tenancy.models import Company
            program = PilotProgram.objects.filter(id=pilot_program_id).first()
            if program is None:
                return Response(
                    {"error": {"code": "PILOT-CHARTER-003", "message": "Pilot program not found."}},
                    status=400,
                )
            if not PilotCharter.objects.filter(
                pilot_program=program, decision=PilotCharter.Decision.AUTHORIZE
            ).exists():
                return Response(
                    {"error": {"code": "PILOT-CHARTER-004", "message": "Pilot program has no signed authorize-charter."}},
                    status=400,
                )
        supersedes = None
        supersedes_id = serializer.validated_data.get("supersedes")
        if supersedes_id:
            supersedes = ExitDecision.objects.filter(id=supersedes_id, phase=phase).first()
        decision = ExitDecision.objects.create(
            phase=phase,
            decision=serializer.validated_data["decision"],
            rationale=serializer.validated_data["rationale"],
            signed_by=request.user,
            supersedes=supersedes,
            metadata=metadata,
        )
        decision.signature_hmac = decision.compute_signature()
        decision.save(update_fields=["signature_hmac"])
        record_audit_event(
            event_type="EXIT_DECISION_SIGNED",
            target_type="exit_decision",
            target_id=str(decision.id),
            actor_id=str(request.user.id),
            metadata={
                "phase": phase,
                "decision": decision.decision,
                "supersedes": str(decision.supersedes_id) if decision.supersedes_id else None,
            },
        )
        return Response(ExitDecisionSerializer(decision).data, status=201)

    @extend_schema(responses=ExitDecisionSerializer(many=True))
    def get(self, request, phase: str):
        decisions = ExitDecision.objects.filter(phase=phase).order_by("-signed_at")
        return Response({"decisions": ExitDecisionSerializer(decisions, many=True).data})
