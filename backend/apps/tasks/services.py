from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.identity.models import User
from apps.organizations.models import Branch, WeeklyShift
from apps.tenancy.access import active_membership_q

from .models import TaskInstance, TaskRecurrenceType, TaskSchedule, TaskTemplate, TaskTemplateVersion, TaskTransferRequest, TaskTransferStatus


TASK_STATUS_PENDING = "pending"
TASK_STATUS_CLAIMED = "claimed"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_CANCELLED = "cancelled"
TASK_STATUS_OVERDUE = "overdue"


TASK_TRANSITIONS: dict[str, set[str]] = {
    TASK_STATUS_PENDING: {TASK_STATUS_PENDING, TASK_STATUS_CLAIMED, TASK_STATUS_IN_PROGRESS, TASK_STATUS_CANCELLED, TASK_STATUS_OVERDUE},
    TASK_STATUS_CLAIMED: {TASK_STATUS_PENDING, TASK_STATUS_IN_PROGRESS, TASK_STATUS_CANCELLED, TASK_STATUS_OVERDUE},
    TASK_STATUS_IN_PROGRESS: {TASK_STATUS_PENDING, TASK_STATUS_COMPLETED, TASK_STATUS_CANCELLED, TASK_STATUS_OVERDUE},
    TASK_STATUS_OVERDUE: {TASK_STATUS_PENDING, TASK_STATUS_CLAIMED, TASK_STATUS_IN_PROGRESS, TASK_STATUS_CANCELLED},
    TASK_STATUS_COMPLETED: set(),
    TASK_STATUS_CANCELLED: set(),
}


def _zone_for_branch(branch: Branch | None) -> ZoneInfo:
    return ZoneInfo(branch.timezone if branch else "UTC")


def _operational_day(local_dt: datetime, cutoff: time) -> date:
    return local_dt.date() if local_dt.time() >= cutoff else local_dt.date() - timedelta(days=1)


def _localize(moment: datetime, branch: Branch | None) -> datetime:
    tz = _zone_for_branch(branch)
    if timezone.is_naive(moment):
        return timezone.make_aware(moment, tz)
    return moment.astimezone(tz)


def _template_version(template: TaskTemplate) -> TaskTemplateVersion:
    version = template.versions.order_by("-version_number", "-created_at").first()
    if version is None:
        raise ValueError("Task template has no version.")
    return version


def transition_task_instance(instance: TaskInstance, target_status: str) -> TaskInstance:
    allowed = TASK_TRANSITIONS.get(instance.status, set())
    if target_status not in allowed:
        raise ValueError(f"Task cannot transition from {instance.status} to {target_status}.")
    instance.status = target_status
    return instance


def _due_datetime(branch: Branch | None, schedule_time: time, moment: datetime) -> datetime:
    local_now = _localize(moment, branch)
    cutoff = branch.operational_day_cutoff if branch else time(0, 0)
    day = _operational_day(local_now, cutoff)
    due_local = datetime.combine(day, schedule_time, tzinfo=local_now.tzinfo)
    return due_local.astimezone(UTC)


def _iter_weekly_shifts(branch: Branch) -> Iterable[WeeklyShift]:
    return WeeklyShift.objects.filter(branch=branch, active=True).select_related("user")


@transaction.atomic
def schedule_due_tasks(moment: datetime | None = None) -> list[TaskInstance]:
    now = moment or timezone.now()
    created: list[TaskInstance] = []
    schedules = TaskSchedule.objects.select_related("company", "branch", "template").filter(active=True)
    for schedule in schedules:
        branch = schedule.branch
        if schedule.recurrence_type in {TaskRecurrenceType.DAILY_FIXED, TaskRecurrenceType.WEEKLY_FIXED} and not schedule.scheduled_time:
            continue
        if schedule.recurrence_type == TaskRecurrenceType.DAILY_FIXED:
            due_at = _due_datetime(branch, schedule.scheduled_time, now)
            if due_at <= now:
                created.append(_create_instance(schedule, due_at, now))
        elif schedule.recurrence_type == TaskRecurrenceType.WEEKLY_FIXED:
            local_now = _localize(now, branch)
            if schedule.weekday is None or schedule.weekday != local_now.weekday():
                continue
            due_at = _due_datetime(branch, schedule.scheduled_time, now)
            if due_at <= now:
                created.append(_create_instance(schedule, due_at, now))
        else:
            if branch is None:
                continue
            local_now = _localize(now, branch)
            for shift in _iter_weekly_shifts(branch):
                if shift.weekday != local_now.weekday():
                    continue
                base = datetime.combine(local_now.date(), shift.start_time, tzinfo=local_now.tzinfo)
                due_local = base + timedelta(minutes=schedule.shift_offset_minutes)
                due_at = due_local.astimezone(UTC)
                if due_at <= now:
                    instance = _create_instance(schedule, due_at, now, assigned_user=shift.user)
                    created.append(instance)
    return created


@transaction.atomic
def mark_overdue_tasks(moment: datetime | None = None) -> list[TaskInstance]:
    now = moment or timezone.now()
    overdue_instances = list(
        TaskInstance.objects.select_for_update().filter(
            due_at__lt=now,
            status__in=[TASK_STATUS_PENDING, TASK_STATUS_CLAIMED, TASK_STATUS_IN_PROGRESS],
        )
    )
    updated: list[TaskInstance] = []
    for instance in overdue_instances:
        if instance.status == TASK_STATUS_OVERDUE:
            continue
        transition_task_instance(instance, TASK_STATUS_OVERDUE)
        instance.overdue_at = instance.overdue_at or now
        instance.save(update_fields=["status", "overdue_at", "updated_at"])
        updated.append(instance)
        record_audit_event(
            event_type="TASK_INSTANCE_OVERDUE",
            target_type="task_instance",
            target_id=str(instance.id),
            actor_id="",
            branch_id=str(instance.branch_id),
            metadata={"due_at": instance.due_at.isoformat()},
        )
    return updated


def _create_instance(
    schedule: TaskSchedule,
    due_at: datetime,
    moment: datetime,
    assigned_user: User | None = None,
) -> TaskInstance:
    version = _template_version(schedule.template)
    branch = schedule.branch or Branch.objects.filter(company=schedule.company).first()
    if branch is None:
        raise ValueError("Task schedule requires a branch.")
    instance, created = TaskInstance.objects.get_or_create(
        schedule=schedule,
        scheduled_for=due_at,
        defaults={
            "company": schedule.company,
            "branch": branch,
            "template": schedule.template,
            "template_version": version,
            "due_at": due_at,
            "assigned_user": assigned_user or schedule.template.assigned_user,
            "status": TASK_STATUS_PENDING,
        },
    )
    if created:
        record_audit_event(
            event_type="TASK_INSTANCE_CREATED",
            target_type="task_instance",
            target_id=str(instance.id),
            actor_id="",
            metadata={"schedule_id": str(schedule.id), "scheduled_for": due_at.isoformat()},
        )
    schedule.last_generated_at = moment
    schedule.save(update_fields=["last_generated_at"])
    return instance


@transaction.atomic
def claim_task(instance_id: str, user: User) -> TaskInstance:
    instance = TaskInstance.objects.select_for_update().select_related("company", "branch").get(id=instance_id)
    if instance.assigned_user_id not in {None, user.id} and instance.status != TASK_STATUS_OVERDUE:
        raise ValueError("Task is assigned to another user.")
    transition_task_instance(instance, TASK_STATUS_CLAIMED)
    instance.claimed_by = user
    instance.assigned_user = user
    instance.save(update_fields=["status", "claimed_by", "assigned_user", "updated_at"])
    record_audit_event(
        event_type="TASK_INSTANCE_CLAIMED",
        target_type="task_instance",
        target_id=str(instance.id),
        actor_id=str(user.id),
        branch_id=str(instance.branch_id),
    )
    return instance


@transaction.atomic
def start_task(instance_id: str, user: User) -> TaskInstance:
    instance = TaskInstance.objects.select_for_update().get(id=instance_id)
    if instance.assigned_user_id not in {None, user.id} and instance.claimed_by_id != user.id:
        raise ValueError("Task is assigned to another user.")
    if instance.status == TASK_STATUS_PENDING and instance.assigned_user_id not in {None, user.id}:
        raise ValueError("Task must be claimed before starting.")
    transition_task_instance(instance, TASK_STATUS_IN_PROGRESS)
    instance.claimed_by = instance.claimed_by or user
    instance.started_at = timezone.now()
    instance.save(update_fields=["status", "claimed_by", "started_at", "updated_at"])
    record_audit_event(
        event_type="TASK_INSTANCE_STARTED",
        target_type="task_instance",
        target_id=str(instance.id),
        actor_id=str(user.id),
        branch_id=str(instance.branch_id),
    )
    return instance


@transaction.atomic
def complete_task(instance_id: str, user: User) -> TaskInstance:
    instance = TaskInstance.objects.select_for_update().get(id=instance_id)
    if instance.assigned_user_id not in {None, user.id} and instance.claimed_by_id != user.id:
        raise ValueError("Task is assigned to another user.")
    if instance.status not in {TASK_STATUS_CLAIMED, TASK_STATUS_IN_PROGRESS, TASK_STATUS_OVERDUE}:
        raise ValueError("Task cannot be completed.")
    transition_task_instance(instance, "completed")
    instance.completed_at = timezone.now()
    instance.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit_event(
        event_type="TASK_INSTANCE_COMPLETED",
        target_type="task_instance",
        target_id=str(instance.id),
        actor_id=str(user.id),
        branch_id=str(instance.branch_id),
    )
    return instance


@transaction.atomic
def request_transfer(instance_id: str, requested_by: User, requested_to: User, reason: str = "") -> TaskTransferRequest:
    instance = TaskInstance.objects.select_related("company", "branch").get(id=instance_id)
    # H-07 / tenant isolation: the requester and target must share a
    # company with the task instance, otherwise a cross-tenant transfer
    # record would be persisted. Reject explicitly with a ValueError that
    # the API layer converts to a 4xx response.
    if instance.company_id is None:
        raise ValueError("Task instance is missing a company scope.")
    requester_company_ids = set(
        requested_by.company_memberships.filter(active=True).filter(active_membership_q()).values_list("company_id", flat=True)
    )
    if instance.company.owner_id == requested_by.id:
        requester_company_ids.add(instance.company_id)
    if instance.company_id not in requester_company_ids:
        raise ValueError("Task instance is outside the requester's company.")
    if requested_to.id != instance.assigned_user_id and not instance.company.memberships.filter(
        active=True, user=requested_to
    ).filter(
        active_membership_q()
    ).exists() and instance.company.owner_id != requested_to.id:
        raise ValueError("Transfer target is outside the task instance's company.")
    transfer = TaskTransferRequest.objects.create(
        task_instance=instance,
        requested_by=requested_by,
        requested_to=requested_to,
        reason=reason,
    )
    record_audit_event(
        event_type="TASK_TRANSFER_REQUESTED",
        target_type="task_instance",
        target_id=str(instance.id),
        actor_id=str(requested_by.id),
        branch_id=str(instance.branch_id),
        metadata={"transfer_request_id": str(transfer.id), "requested_to": str(requested_to.id)},
    )
    return transfer


@transaction.atomic
def resolve_transfer(transfer_id: str, decided_by: User, approved: bool) -> TaskTransferRequest:
    transfer = (
        TaskTransferRequest.objects.select_for_update()
        .select_related("task_instance", "task_instance__company")
        .get(id=transfer_id)
    )
    if transfer.status != TaskTransferStatus.PENDING:
        raise ValueError("Transfer request already resolved.")
    company = transfer.task_instance.company
    if company is None:
        raise ValueError("Transfer request is missing a company scope.")
    # Defence in depth: the view already filters by company, but the
    # service layer must also reject decisions from outside the company
    # so future callers cannot bypass the view filter.
    decided_is_member = company.owner_id == decided_by.id or company.memberships.filter(
        active=True,
        user=decided_by,
    ).filter(active_membership_q()).exists()
    if not decided_is_member and decided_by.id != transfer.requested_to_id:
        raise ValueError("Only company members can resolve this transfer.")
    transfer.status = TaskTransferStatus.APPROVED if approved else TaskTransferStatus.REJECTED
    transfer.decided_by = decided_by
    transfer.decided_at = timezone.now()
    transfer.save(update_fields=["status", "decided_by", "decided_at"])
    if approved:
        task = transfer.task_instance
        task.assigned_user = transfer.requested_to
        task.claimed_by = None
        task.started_at = None
        transition_task_instance(task, TASK_STATUS_PENDING)
        task.save(update_fields=["assigned_user", "claimed_by", "started_at", "status", "updated_at"])
    record_audit_event(
        event_type="TASK_TRANSFER_RESOLVED",
        target_type="task_transfer_request",
        target_id=str(transfer.id),
        actor_id=str(decided_by.id),
        branch_id=str(transfer.task_instance.branch_id),
        metadata={"approved": approved},
    )
    return transfer


@transaction.atomic
def cancel_task(instance_id: str, actor: User, reason: str) -> TaskInstance:
    instance = TaskInstance.objects.select_for_update().get(id=instance_id)
    if instance.status == TASK_STATUS_CANCELLED:
        return instance
    transition_task_instance(instance, TASK_STATUS_CANCELLED)
    instance.cancelled_at = timezone.now()
    instance.cancel_reason = reason
    instance.save(update_fields=["status", "cancelled_at", "cancel_reason", "updated_at"])
    record_audit_event(
        event_type="TASK_INSTANCE_CANCELLED",
        target_type="task_instance",
        target_id=str(instance.id),
        actor_id=str(actor.id),
        branch_id=str(instance.branch_id),
        metadata={"reason": reason},
    )
    return instance
