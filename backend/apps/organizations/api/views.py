from __future__ import annotations

from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.audit.services import record_audit_event
from apps.platform_core.errors import platform_service_call
from apps.platform_core.mixins import TenantAPIView
from apps.tenancy.serializers import CompanyMembershipSerializer
from apps.tenancy.services import ensure_company_operational

from ..models import Branch, CompanyMembership, CompanyRole, JobRole, WeeklyShift
from ..serializers import (
    BranchCreateSerializer,
    BranchSerializer,
    JobRoleSerializer,
    RoleCreateSerializer,
    WeeklyShiftCreateSerializer,
    WeeklyShiftSerializer,
)


class BranchesView(TenantAPIView):
    # BE-01: Branches are visible to every role in the active company so
    # employees can pick the branch they work at; only OWNER can create
    # a new one (in-method check).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="List of company branches."))
    def get(self, request):
        company = self.get_tenant().company
        return Response({"branches": BranchSerializer(Branch.objects.filter(company=company), many=True).data})

    @extend_schema(request=BranchCreateSerializer, responses={201: BranchSerializer})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        context.require_roles(CompanyRole.OWNER)
        company = context.company
        try:
            ensure_company_operational(company)
        except ValueError as exc:
            from apps.platform_core.errors import PlatformAPIException
            raise PlatformAPIException(str(exc)) from exc
        serializer = BranchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = Branch.objects.create(company=company, **serializer.validated_data)
        record_audit_event(
            event_type="BRANCH_CREATED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(request.user.id),
            metadata={"branch_id": str(branch.id)},
        )
        return Response(BranchSerializer(branch).data, status=201)


class JobRolesView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="List of job roles."))
    def get(self, request):
        company = self.get_tenant().company
        return Response({"roles": JobRoleSerializer(JobRole.objects.filter(company=company), many=True).data})

    @extend_schema(request=RoleCreateSerializer, responses={201: JobRoleSerializer})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        context.require_roles(CompanyRole.OWNER)
        company = context.company
        try:
            ensure_company_operational(company)
        except ValueError as exc:
            from apps.platform_core.errors import PlatformAPIException
            raise PlatformAPIException(str(exc)) from exc
        serializer = RoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = JobRole.objects.create(company=company, **serializer.validated_data)
        record_audit_event(
            event_type="JOB_ROLE_CREATED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(request.user.id),
            metadata={"role_id": str(role.id)},
        )
        return Response(JobRoleSerializer(role).data, status=201)


class MembershipsView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="List of company memberships."))
    def get(self, request):
        company = self.get_tenant().company
        memberships = CompanyMembership.objects.filter(company=company).select_related("user")
        return Response({"memberships": CompanyMembershipSerializer(memberships, many=True).data})


class WeeklyShiftsView(TenantAPIView):
    # BE-01: Weekly shifts are a management artifact; OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="List of weekly shifts for the active company."))
    def get(self, request):
        company = self.get_tenant().company
        return Response(
            {"shifts": WeeklyShiftSerializer(WeeklyShift.objects.filter(company=company), many=True).data}
        )

    @extend_schema(request=WeeklyShiftCreateSerializer, responses={201: WeeklyShiftSerializer})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        context.require_roles(CompanyRole.OWNER)
        company = context.company
        try:
            ensure_company_operational(company)
        except ValueError as exc:
            from apps.platform_core.errors import PlatformAPIException
            raise PlatformAPIException(str(exc)) from exc
        serializer = WeeklyShiftCreateSerializer(data=request.data, company=company)
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        # ``branch_id`` and ``user_id`` were inputs; the model needs
        # ``branch`` and ``user``. We resolved them inside ``validate`` and
        # stored them as auxiliary keys to keep the response payload
        # identical to the historical contract.
        branch = validated.pop("branch")
        user_id = validated.pop("user_id_resolved")
        validated.pop("branch_id", None)
        validated.pop("user_id", None)
        shift = WeeklyShift.objects.create(
            company=company,
            branch=branch,
            user_id=user_id,
            weekday=validated["weekday"],
            start_time=validated["start_time"],
            end_time=validated["end_time"],
        )
        record_audit_event(
            event_type="WEEKLY_SHIFT_CREATED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(request.user.id),
            metadata={"shift_id": str(shift.id)},
        )
        return Response(WeeklyShiftSerializer(shift).data, status=201)
