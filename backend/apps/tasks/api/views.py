from __future__ import annotations

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.organizations.models import Branch, CompanyRole
from apps.platform_core.errors import platform_service_call, PlatformAPIException, PlatformPermissionException
from apps.platform_core.mixins import TenantAPIView
from apps.tenancy.access import require_company_user, validate_company_reference
from apps.tenancy.services import ensure_company_operational

from ..models import TaskInstance, TaskSchedule, TaskTemplate, TaskTransferRequest
from ..serializers import (
    TaskInstanceSerializer,
    TaskScheduleCreateSerializer,
    TaskScheduleSerializer,
    TaskTemplateCreateSerializer,
    TaskTemplateSerializer,
    TaskTransitionSerializer,
    TaskTransferRequestSerializer,
)
from ..services import (
    cancel_task,
    claim_task,
    complete_task,
    request_transfer,
    resolve_transfer,
    start_task,
)


def _operational_company(context):
    try:
        ensure_company_operational(context.company)
    except ValueError as exc:
        raise PlatformPermissionException(str(exc)) from exc
    return context.company


class TaskTemplatesView(TenantAPIView):
    # BE-01: Task templates are visible to every role in the active
    # company so employees can find their assigned work. Only OWNER +
    # MONITOR can create (in-method check on POST).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="List of task templates."))

    @platform_service_call
    def get(self, request):
        context = self.get_tenant()
        templates = TaskTemplate.objects.filter(company=context.company).filter(
            branch_id__in=context.branch_ids
        ).select_related("branch", "assigned_user")
        return Response({"templates": TaskTemplateSerializer(templates, many=True).data})

    @extend_schema(request=TaskTemplateCreateSerializer, responses={201: TaskTemplateSerializer})

    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        context.require_roles(CompanyRole.OWNER, CompanyRole.MONITOR)
        company = _operational_company(context)
        serializer = TaskTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        if payload["company_id"] != company.id:
            raise PlatformPermissionException("The requested company does not match the active company.")
        branch_id = payload.get("branch_id")
        if branch_id is not None:
            get_object_or_404(Branch, id=branch_id, company=company, active=True)
            context.require_branch(branch_id)
        assigned_user_id = payload.get("assigned_user_id")
        if assigned_user_id is not None:
            require_company_user(context, assigned_user_id)
        template = TaskTemplate.objects.create(
            company=company,
            branch_id=payload.get("branch_id"),
            slug=payload["slug"],
            name=payload["name"],
            description=payload.get("description", ""),
            assignment_mode=payload["assignment_mode"],
            assigned_user_id=payload.get("assigned_user_id"),
            assigned_role_code=payload.get("assigned_role_code", ""),
            risk_level=payload.get("risk_level", "low"),
            task_weight=payload.get("task_weight", 1),
        )
        return Response(TaskTemplateSerializer(template).data, status=201)


class TaskSchedulesView(TenantAPIView):
    # BE-01: Task schedules are a tenant-wide concern; visible to every
    # role so an employee can see when the next shift of a template
    # starts. The POST is restricted via the in-method role check.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="List of task schedules."))

    @platform_service_call
    def get(self, request):
        context = self.get_tenant()
        schedules = TaskSchedule.objects.filter(company=context.company).filter(
            branch_id__in=context.branch_ids
        ).select_related("template", "branch")
        return Response({"schedules": TaskScheduleSerializer(schedules, many=True).data})

    @extend_schema(request=TaskScheduleCreateSerializer, responses={201: TaskScheduleSerializer})

    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        context.require_roles(CompanyRole.OWNER, CompanyRole.MONITOR)
        company = _operational_company(context)
        serializer = TaskScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        if payload["company_id"] != company.id:
            raise PlatformPermissionException("The requested company does not match the active company.")
        template = get_object_or_404(
            TaskTemplate,
            id=payload["template_id"],
            company=company,
            active=True,
        )
        branch_id = payload.get("branch_id")
        if branch_id is not None:
            get_object_or_404(Branch, id=branch_id, company=company, active=True)
            context.require_branch(branch_id)
        if template.branch_id is not None and template.branch_id != branch_id:
            raise PlatformPermissionException("The schedule branch does not match the task template branch.")
        schedule = TaskSchedule.objects.create(
            company=company,
            branch_id=payload.get("branch_id"),
            template_id=payload["template_id"],
            recurrence_type=payload["recurrence_type"],
            scheduled_time=payload.get("scheduled_time"),
            weekday=payload.get("weekday"),
            shift_offset_minutes=payload.get("shift_offset_minutes", 0),
        )
        return Response(TaskScheduleSerializer(schedule).data, status=201)


class TaskInstancesView(TenantAPIView):
    # BE-01: Task instances are a tenant-wide list; the branch-scoping
    # inside the handler restricts what an employee can see.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="List of task instances."))

    @platform_service_call
    def get(self, request):
        context = self.get_tenant()
        instances = TaskInstance.objects.for_company_and_branches(
            context.company, context.branch_ids,
        ).select_related("template", "branch", "assigned_user")
        return Response({"instances": TaskInstanceSerializer(instances, many=True).data})


class TaskClaimView(TenantAPIView):
    # BE-01: Task claim is a tenant-wide action (an employee can claim
    # the task they are scheduled to work on).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=None, responses=TaskInstanceSerializer)

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        # BE-02: explicitly validate the task reference against the
        # active company so an IDOR probe is converted to a 403 instead
        # of leaking the existence of a task in another tenant through a
        # 404.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        claimed = claim_task(str(instance.id), request.user)
        return Response(TaskInstanceSerializer(claimed).data)


class TaskStartView(TenantAPIView):
    # BE-01: Task start is a tenant-wide action.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=None, responses=TaskInstanceSerializer)

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        # BE-02: see TaskClaimView.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        started = start_task(str(instance_id), request.user)
        return Response(TaskInstanceSerializer(started).data)


class TaskCompleteView(TenantAPIView):
    # BE-01: Task complete is a tenant-wide action.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=None, responses=TaskInstanceSerializer)

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        # BE-02: see TaskClaimView.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        completed = complete_task(str(instance_id), request.user)
        return Response(TaskInstanceSerializer(completed).data)


class TaskCancelView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=TaskTransitionSerializer, responses=TaskInstanceSerializer)

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        # BE-02: see TaskClaimView.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        serializer = TaskTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cancelled = cancel_task(str(instance_id), request.user, serializer.validated_data.get("reason", ""))
        return Response(TaskInstanceSerializer(cancelled).data)


class TaskTransfersView(TenantAPIView):
    # BE-01: Task transfers are a tenant-wide action: an employee can
    # request a transfer for a task they were scheduled on. The
    # in-method ``require_company_user`` keeps the target inside the
    # active company.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=TaskTransitionSerializer, responses={201: TaskTransferRequestSerializer})

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        # BE-02: see TaskClaimView.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        serializer = TaskTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_id = serializer.validated_data.get("requested_to_id")
        if target_id is None:
            raise PlatformAPIException("requested_to_id is required.")
        require_company_user(context, target_id)
        requested_to = get_user_model().objects.get(id=target_id)
        transfer = request_transfer(str(instance.id), request.user, requested_to, serializer.validated_data.get("reason", ""))
        return Response(TaskTransferRequestSerializer(transfer).data, status=201)


class TaskTransfersListView(TenantAPIView):
    # BE-01: Listing task transfers is a tenant-wide view; the
    # branch-scoping inside the handler keeps the list tight.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="List of task transfer requests."))

    @platform_service_call
    def get(self, request):
        context = self.get_tenant()
        transfers = TaskTransferRequest.objects.filter(
            task_instance__company=context.company,
            task_instance__branch_id__in=context.branch_ids,
        ).select_related("task_instance", "requested_by", "requested_to", "decided_by")
        return Response({"transfers": TaskTransferRequestSerializer(transfers, many=True).data})


class TaskTransferResolveView(TenantAPIView):
    # BE-01: Resolving a transfer is a tenant-wide action: the in-method
    # check ensures either the recipient or a management role decides.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=TaskTransitionSerializer, responses=TaskTransferRequestSerializer)

    @platform_service_call
    def post(self, request, transfer_id):
        context = self.get_tenant()
        serializer = TaskTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # BE-02: validate the transfer request against the active company.
        # TaskTransferRequest does not carry a ``company`` FK directly, so
        # we filter through the related ``task_instance__company`` to
        # keep the helper usable here.
        from apps.tasks.models import TaskTransferRequest as _TaskTransferRequest

        transfer = _TaskTransferRequest.objects.select_related("task_instance").filter(
            id=transfer_id,
            task_instance__company=context.company,
        ).first()
        if transfer is None:
            from apps.platform_core.errors import PlatformPermissionException
            raise PlatformPermissionException(
                "Referenced TaskTransferRequest is outside the active company."
            )
        context.require_branch(transfer.task_instance.branch_id)
        if request.user.id != transfer.requested_to_id and context.role not in {
            CompanyRole.OWNER,
            CompanyRole.MONITOR,
        }:
            raise PlatformPermissionException("Only the transfer target or company management can decide this request.")
        transfer = resolve_transfer(str(transfer.id), request.user, serializer.validated_data.get("approved", False))
        return Response(TaskTransferRequestSerializer(transfer).data)


class TaskSchedulerRunView(TenantAPIView):
    # BE-01: Scheduler-run is a management endpoint; the body raises
    # ``PlatformPermissionException`` for tenant users, so we restrict
    # the class to OWNER + MONITOR.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=None, responses=OpenApiResponse(response=dict, description="Created task instances from due schedules."))

    @platform_service_call
    def post(self, request):
        self.get_tenant()
        raise PlatformPermissionException("Scheduler execution is restricted to background workers.")
