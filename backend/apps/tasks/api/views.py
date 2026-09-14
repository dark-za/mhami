from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from apps.organizations.models import Branch, CompanyMembership, CompanyRole, UserBranchMembership
from apps.platform_core.errors import platform_service_call, PlatformAPIException, PlatformPermissionException
from apps.platform_core.mixins import TenantAPIView
from apps.tenancy.access import active_membership_q, require_company_user, validate_company_reference
from apps.tenancy.services import ensure_company_operational

from ..models import TaskInstance, TaskRequest, TaskRequestKind, TaskSchedule, TaskTemplate, TaskTemplateVersion, TaskTransferRequest
from ..serializers import (
    TaskInstanceSerializer,
    TaskRequestCreateSerializer,
    TaskRequestDecisionSerializer,
    TaskRequestSerializer,
    TaskScheduleCreateSerializer,
    TaskScheduleSerializer,
    ScheduledTaskCreateSerializer,
    TaskTemplateCreateSerializer,
    TaskTemplateSerializer,
    TaskTemplateVersionCreateSerializer,
    TaskTemplateVersionSerializer,
    TaskTransitionSerializer,
    TaskTransferRecipientSerializer,
    TaskTransferRequestSerializer,
)
from ..services import (
    cancel_task,
    claim_task,
    complete_task,
    create_task_request,
    request_transfer,
    resolve_transfer,
    resolve_task_request,
    start_task,
)


def _operational_company(context):
    try:
        ensure_company_operational(context.company)
    except ValueError as exc:
        raise PlatformPermissionException(str(exc)) from exc
    return context.company


def _unique_task_slug(company, requested_slug: str | None, name: str) -> str:
    base = slugify(requested_slug or name)[:80].strip("-") or "task"
    slug = base
    suffix = 1
    while TaskTemplate.objects.filter(company=company, slug=slug).exists():
        suffix += 1
        slug = f"{base[:88]}-{suffix}"
    return slug


def _validate_branch_assignment(context, branch_id, assigned_user_id):
    company = context.company
    branch = validate_company_reference(
        company,
        Branch,
        branch_id,
        extra_filters={"active": True},
    )
    context.require_branch(branch.id)
    require_company_user(context, assigned_user_id)
    if not UserBranchMembership.objects.filter(
        company=company,
        user_id=assigned_user_id,
        branch=branch,
        active=True,
    ).filter(active_membership_q()).exists():
        raise PlatformPermissionException("Assigned user must be active in the task branch.")
    return branch


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
        )
        if context.role == CompanyRole.EMPLOYEE:
            templates = templates.filter(assigned_user=request.user)
        templates = templates.select_related("branch", "assigned_user")
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
        if context.role == CompanyRole.MONITOR and branch_id is None:
            raise PlatformPermissionException("Monitors must create templates inside an assigned branch.")
        if branch_id is not None:
            get_object_or_404(Branch, id=branch_id, company=company, active=True)
            context.require_branch(branch_id)
        assigned_user_id = payload.get("assigned_user_id")
        if assigned_user_id is not None:
            require_company_user(context, assigned_user_id)
            if branch_id is not None and not UserBranchMembership.objects.filter(
                company=company,
                user_id=assigned_user_id,
                branch_id=branch_id,
                active=True,
            ).filter(active_membership_q()).exists():
                raise PlatformPermissionException("Assigned user must be active in the task branch.")
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


class TaskTemplateVersionsView(TenantAPIView):
    """Create immutable task instructions before a schedule can generate work."""

    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="Versions for a task template."))
    def get(self, request, template_id):
        context = self.get_tenant()
        template = validate_company_reference(context.company, TaskTemplate, template_id)
        if template.branch_id is not None:
            context.require_branch(template.branch_id)
        elif context.role == CompanyRole.MONITOR:
            raise PlatformPermissionException("Monitors cannot access global task templates.")
        versions = template.versions.order_by("-version_number")
        return Response({"versions": TaskTemplateVersionSerializer(versions, many=True).data})

    @extend_schema(request=TaskTemplateVersionCreateSerializer, responses={201: TaskTemplateVersionSerializer})
    @platform_service_call
    def post(self, request, template_id):
        context = self.get_tenant()
        serializer = TaskTemplateVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            template = TaskTemplate.objects.select_for_update().get(id=template_id, company=context.company)
            if template.branch_id is not None:
                context.require_branch(template.branch_id)
            elif context.role == CompanyRole.MONITOR:
                raise PlatformPermissionException("Monitors cannot change global task templates.")
            next_version = (template.versions.aggregate(latest=Max("version_number"))["latest"] or 0) + 1
            payload = serializer.validated_data
            version = TaskTemplateVersion.objects.create(
                template=template,
                version_number=next_version,
                instructions=payload["instructions"],
                checklist_definition=payload.get("checklist_definition", []),
                evidence_requirements=payload.get("evidence_requirements", []),
                reference_instructions=payload.get("reference_instructions", ""),
                risk_level=payload.get("risk_level", template.risk_level),
            )
        return Response(TaskTemplateVersionSerializer(version).data, status=201)


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
        )
        if context.role == CompanyRole.EMPLOYEE:
            schedules = schedules.filter(template__assigned_user=request.user)
        schedules = schedules.select_related("template", "branch")
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
        if context.role == CompanyRole.MONITOR and branch_id is None:
            raise PlatformPermissionException("Monitors must create schedules inside an assigned branch.")
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


class ScheduledTaskCreateView(TenantAPIView):
    """Create a named-user template, first version, and schedule atomically."""

    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(
        request=ScheduledTaskCreateSerializer,
        responses=inline_serializer(
            name="ScheduledTaskCreateResponse",
            fields={
                "template": TaskTemplateSerializer(),
                "version": TaskTemplateVersionSerializer(),
                "schedule": TaskScheduleSerializer(),
            },
        ),
    )
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        context.require_roles(CompanyRole.OWNER, CompanyRole.MONITOR)
        company = _operational_company(context)
        serializer = ScheduledTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        branch = _validate_branch_assignment(
            context,
            payload["branch_id"],
            payload["assigned_user_id"],
        )
        with transaction.atomic():
            template = TaskTemplate.objects.create(
                company=company,
                branch=branch,
                slug=_unique_task_slug(company, payload.get("slug"), payload["name"]),
                name=payload["name"],
                description=payload.get("description", ""),
                assignment_mode="named_user",
                assigned_user_id=payload["assigned_user_id"],
                risk_level=payload.get("risk_level", "low"),
                task_weight=payload.get("task_weight", 1),
            )
            version = TaskTemplateVersion.objects.create(
                template=template,
                version_number=1,
                instructions=payload["instructions"],
                checklist_definition=payload.get("checklist_definition", []),
                evidence_requirements=payload.get("evidence_requirements", []),
                reference_instructions=payload.get("reference_instructions", ""),
                risk_level=payload.get("risk_level", template.risk_level),
            )
            schedule = TaskSchedule.objects.create(
                company=company,
                branch=branch,
                template=template,
                recurrence_type=payload["recurrence_type"],
                scheduled_time=payload.get("scheduled_time"),
                weekday=payload.get("weekday"),
                shift_offset_minutes=payload.get("shift_offset_minutes", 0),
            )
        return Response({
            "template": TaskTemplateSerializer(template).data,
            "version": TaskTemplateVersionSerializer(version).data,
            "schedule": TaskScheduleSerializer(schedule).data,
        }, status=201)


class TaskInstancesView(TenantAPIView):
    # BE-01: Task instances are a tenant-wide list; the branch-scoping
    # inside the handler restricts what an employee can see.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="List of task instances."))

    @platform_service_call
    def get(self, request):
        context = self.get_tenant()
        if context.role == CompanyRole.EMPLOYEE:
            if not context.branch_ids:
                instances = TaskInstance.objects.none().select_related("template", "branch", "assigned_user")
                return Response({"instances": TaskInstanceSerializer(instances, many=True).data})
            queryset = TaskInstance.objects.filter(
                company=context.company,
                branch_id__in=context.branch_ids,
                assigned_user=request.user,
            )
        else:
            queryset = TaskInstance.objects.for_company_and_branches(
                context.company, context.branch_ids,
            )
        instances = queryset.select_related("template", "branch", "assigned_user")
        return Response({"instances": TaskInstanceSerializer(instances, many=True).data})


class TaskClaimView(TenantAPIView):
    # BE-01: Task claim is restricted to owner/monitor (branch-scoped).
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=None, responses=TaskInstanceSerializer)

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        context.require_roles(CompanyRole.OWNER, CompanyRole.MONITOR)
        # BE-02: explicitly validate the task reference against the
        # active company so an IDOR probe is converted to a 403 instead
        # of leaking the existence of a task in another tenant through a
        # 404.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        claimed = claim_task(str(instance.id), request.user)
        return Response(TaskInstanceSerializer(claimed).data)


class TaskStartView(TenantAPIView):
    # BE-01: Task start is a tenant-wide action; employees may act only on own tasks.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=None, responses=TaskInstanceSerializer)

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        # BE-02: see TaskClaimView.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        if context.role == CompanyRole.EMPLOYEE and instance.assigned_user_id != request.user.id:
            raise PlatformPermissionException("Employees may start only tasks assigned to themselves.")
        started = start_task(str(instance_id), request.user)
        return Response(TaskInstanceSerializer(started).data)


class TaskCompleteView(TenantAPIView):
    # BE-01: Task complete is a tenant-wide action; employees may act only on own tasks.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=None, responses=TaskInstanceSerializer)

    @platform_service_call
    def post(self, request, instance_id):
        context = self.get_tenant()
        # BE-02: see TaskClaimView.
        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        if context.role == CompanyRole.EMPLOYEE and instance.assigned_user_id != request.user.id:
            raise PlatformPermissionException("Employees may complete only tasks assigned to themselves.")
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
        if context.role == CompanyRole.EMPLOYEE and instance.assigned_user_id != request.user.id:
            raise PlatformPermissionException("Employees may request transfer only for tasks assigned to themselves.")
        serializer = TaskTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_id = serializer.validated_data.get("requested_to_id")
        if target_id is None:
            raise PlatformAPIException("requested_to_id is required.")
        require_company_user(context, target_id)
        # Transfer target must have an active branch assignment to the task's branch.
        has_branch_assignment = UserBranchMembership.objects.filter(
            company=context.company,
            user_id=target_id,
            branch_id=instance.branch_id,
            active=True,
        ).filter(active_membership_q()).exists()
        if not has_branch_assignment:
            raise PlatformPermissionException("Transfer target must be assigned to the task branch.")
        if context.role == CompanyRole.EMPLOYEE:
            target_membership = (
                CompanyMembership.objects.filter(company=context.company, user_id=target_id, active=True)
                .filter(active_membership_q())
                .first()
            )
            if target_membership is None or target_membership.role != CompanyRole.EMPLOYEE:
                raise PlatformPermissionException("Transfer target must be an active employee in the same organization.")
        requested_to = get_user_model().objects.get(id=target_id)
        transfer = request_transfer(str(instance.id), request.user, requested_to, serializer.validated_data.get("reason", ""))
        return Response(TaskTransferRequestSerializer(transfer).data, status=201)


class TaskTransferRecipientsView(TenantAPIView):
    """Return only employees eligible to receive one visible task."""

    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(
        responses=inline_serializer(
            name="TaskTransferRecipientList",
            fields={"recipients": TaskTransferRecipientSerializer(many=True)},
        )
    )
    @platform_service_call
    def get(self, request):
        context = self.get_tenant()
        instance_id = request.query_params.get("task_instance_id")
        if not instance_id:
            raise PlatformAPIException("task_instance_id is required.")

        instance = validate_company_reference(context.company, TaskInstance, instance_id)
        context.require_branch(instance.branch_id)
        if context.role == CompanyRole.EMPLOYEE and instance.assigned_user_id != request.user.id:
            raise PlatformPermissionException("Employees may view recipients only for tasks assigned to themselves.")

        from django.db.models import Exists, OuterRef

        memberships = (
            CompanyMembership.objects.filter(
                company=context.company,
                role=CompanyRole.EMPLOYEE,
                active=True,
            )
            .filter(active_membership_q())
            .exclude(user=request.user)
            .filter(
                Exists(
                    UserBranchMembership.objects.filter(
                        company=context.company,
                        user_id=OuterRef("user_id"),
                        branch_id=instance.branch_id,
                        active=True,
                    ).filter(active_membership_q())
                )
            )
            .select_related("user")
            .order_by("user__display_name", "user__login_id")
        )
        recipients = [
            {"id": membership.user_id, "display_name": membership.user.display_name or membership.user.login_id}
            for membership in memberships
        ]
        return Response({"recipients": TaskTransferRecipientSerializer(recipients, many=True).data})


class TaskTransfersListView(TenantAPIView):
    # BE-01: Listing task transfers is a tenant-wide view; the
    # branch-scoping inside the handler keeps the list tight.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="List of task transfer requests."))

    @platform_service_call
    def get(self, request):
        context = self.get_tenant()
        base_qs = TaskTransferRequest.objects.filter(
            task_instance__company=context.company,
        ).select_related("task_instance", "requested_by", "requested_to", "decided_by")
        if context.role == CompanyRole.EMPLOYEE:
            from django.db.models import Q

            transfers = base_qs.filter(
                Q(task_instance__assigned_user=request.user) | Q(requested_by=request.user)
            )
        else:
            transfers = base_qs.filter(task_instance__branch_id__in=context.branch_ids)
        return Response({"transfers": TaskTransferRequestSerializer(transfers, many=True).data})


class TaskTransferResolveView(TenantAPIView):
    # A recipient may request a transfer but only company management can
    # approve or reject it. This keeps workflow decisions auditable.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

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
        transfer = resolve_transfer(str(transfer.id), request.user, serializer.validated_data.get("approved", False))
        return Response(TaskTransferRequestSerializer(transfer).data)


class TaskRequestsView(TenantAPIView):
    """Employee requests for a task exception, reassignment, or suggestion."""

    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="Task requests within the active user's scope."))
    def get(self, request):
        context = self.get_tenant()
        requests = TaskRequest.objects.filter(company=context.company).select_related(
            "task_instance", "requested_by", "requested_to", "decided_by"
        )
        if context.role == CompanyRole.EMPLOYEE:
            requests = requests.filter(requested_by=request.user)
        else:
            requests = requests.filter(branch_id__in=context.branch_ids)
        return Response({"requests": TaskRequestSerializer(requests.order_by("-created_at"), many=True).data})

    @extend_schema(request=TaskRequestCreateSerializer, responses={201: TaskRequestSerializer})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        if context.role != CompanyRole.EMPLOYEE:
            raise PlatformPermissionException("Task requests are submitted by employees.")
        serializer = TaskRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        branch = validate_company_reference(context.company, Branch, payload["branch_id"])
        context.require_branch(branch.id)
        task_instance = None
        task_instance_id = payload.get("task_instance_id")
        kind = payload["kind"]
        if kind != TaskRequestKind.TASK_SUGGESTION and task_instance_id is None:
            raise PlatformAPIException("This request type requires a task instance.")
        if task_instance_id is not None:
            task_instance = validate_company_reference(context.company, TaskInstance, task_instance_id)
            if task_instance.branch_id != branch.id:
                raise PlatformPermissionException("Task request branch does not match the task instance.")
            if task_instance.assigned_user_id != request.user.id:
                raise PlatformPermissionException("Employees may request changes only for their assigned tasks.")

        requested_to = None
        target_id = payload.get("requested_to_id")
        if kind == TaskRequestKind.TRANSFER:
            if target_id is None:
                raise PlatformAPIException("A transfer request requires a receiving employee.")
            require_company_user(context, target_id)
            target_membership = CompanyMembership.objects.filter(
                company=context.company,
                user_id=target_id,
                role=CompanyRole.EMPLOYEE,
                active=True,
            ).filter(active_membership_q()).first()
            target_in_branch = UserBranchMembership.objects.filter(
                company=context.company,
                user_id=target_id,
                branch=branch,
                active=True,
            ).filter(active_membership_q()).exists()
            if target_membership is None or not target_in_branch:
                raise PlatformPermissionException("Transfer target must be an active employee in the same branch.")
            requested_to = get_user_model().objects.get(id=target_id)
        elif target_id is not None:
            raise PlatformAPIException("Only transfer requests may name a receiving employee.")

        task_request = create_task_request(
            company=context.company,
            branch=branch,
            task_instance=task_instance,
            requested_by=request.user,
            requested_to=requested_to,
            kind=kind,
            reason=payload["reason"],
        )
        return Response(TaskRequestSerializer(task_request).data, status=201)


class TaskRequestResolveView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=TaskRequestDecisionSerializer, responses=TaskRequestSerializer)
    @platform_service_call
    def post(self, request, task_request_id):
        context = self.get_tenant()
        task_request = TaskRequest.objects.filter(id=task_request_id, company=context.company).first()
        if task_request is None:
            raise PlatformPermissionException("Referenced task request is outside the active company.")
        context.require_branch(task_request.branch_id)
        serializer = TaskRequestDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resolved = resolve_task_request(
            str(task_request.id),
            decided_by=request.user,
            approved=serializer.validated_data["approved"],
            decision_reason=serializer.validated_data.get("decision_reason", ""),
        )
        return Response(TaskRequestSerializer(resolved).data)


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
