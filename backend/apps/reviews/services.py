from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.evidence.models import EvidenceItem, EvidenceStatus, TaskIssueReport
from apps.identity.models import User
from apps.tasks.models import TaskInstance, TaskStatus
from apps.tasks.services import cancel_task
from apps.tenancy.access import accessible_company_branch_ids
from apps.tenancy.models import Company

from .models import ReviewDecision, ReviewDecisionType, ReviewPolicySetting


def accessible_branch_ids(company: Company, user: User) -> list[str]:
    return accessible_company_branch_ids(company, user)


def policy_for_company(company: Company) -> ReviewPolicySetting:
    policy, _created = ReviewPolicySetting.objects.get_or_create(company=company)
    return policy


def review_queue(company: Company, user: User) -> list[dict[str, object]]:
    branch_ids = accessible_branch_ids(company, user)
    now = timezone.now()
    task_items = TaskInstance.objects.filter(company=company, branch_id__in=branch_ids).filter(
        due_at__lt=now,
        status__in=[TaskStatus.PENDING, TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS, TaskStatus.OVERDUE],
    )
    evidence_items = EvidenceItem.objects.filter(company=company, branch_id__in=branch_ids).filter(
        status=EvidenceStatus.NEEDS_REVIEW
    )
    issues = TaskIssueReport.objects.filter(company=company, branch_id__in=branch_ids, resolved_at__isnull=True)
    items: list[dict[str, object]] = []
    for task in task_items.select_related("branch", "template", "assigned_user"):
        items.append(
            {
                "kind": "task",
                "id": str(task.id),
                "branch_id": str(task.branch_id),
                "branch_name": task.branch.name,
                "title": task.template.name,
                "status": task.status,
                "reason": "Overdue or pending review",
                "created_at": task.created_at.isoformat(),
                "task_instance_id": str(task.id),
            }
        )
    for evidence in evidence_items.select_related("branch", "task_instance", "submitted_by"):
        items.append(
            {
                "kind": "evidence",
                "id": str(evidence.id),
                "branch_id": str(evidence.branch_id),
                "branch_name": evidence.branch.name,
                "title": f"{evidence.evidence_type} evidence",
                "status": evidence.status,
                "reason": f"Duplicate risk {evidence.duplicate_risk_score}",
                "created_at": evidence.created_at.isoformat(),
                "evidence_item_id": str(evidence.id),
            }
        )
    for issue in issues.select_related("branch", "task_instance", "submitted_by"):
        items.append(
            {
                "kind": "issue",
                "id": str(issue.id),
                "branch_id": str(issue.branch_id),
                "branch_name": issue.branch.name,
                "title": issue.note[:80],
                "status": "open",
                "reason": "Needs monitor review",
                "created_at": issue.created_at.isoformat(),
                "issue_report_id": str(issue.id),
            }
        )
    return sorted(items, key=lambda item: str(item["created_at"]), reverse=True)


def dashboard_summary(company: Company, user: User) -> dict[str, object]:
    branch_ids = accessible_branch_ids(company, user)
    now = timezone.now()
    start_of_day = timezone.make_aware(timezone.datetime.combine(now.date(), timezone.datetime.min.time()))
    tasks = TaskInstance.objects.filter(company=company, branch_id__in=branch_ids)
    branches = list(company.branches.filter(id__in=branch_ids))
    branch_summaries = []
    for branch in branches:
        branch_tasks = tasks.filter(branch=branch)
        branch_summaries.append(
            {
                "branch_id": str(branch.id),
                "branch_name": branch.name,
                "completed_today": branch_tasks.filter(completed_at__gte=start_of_day).count(),
                "overdue": branch_tasks.filter(status=TaskStatus.OVERDUE).count(),
                "quality_exceptions": EvidenceItem.objects.filter(branch=branch, status=EvidenceStatus.NEEDS_REVIEW).count(),
            }
        )
    completed_today = tasks.filter(completed_at__gte=start_of_day).count()
    overdue = tasks.filter(status=TaskStatus.OVERDUE).count()
    open_issues = TaskIssueReport.objects.filter(company=company, branch_id__in=branch_ids, resolved_at__isnull=True).count()
    pending_review = EvidenceItem.objects.filter(company=company, branch_id__in=branch_ids, status=EvidenceStatus.NEEDS_REVIEW).count()
    total_quality_exceptions = pending_review + open_issues
    company_status = company.status
    trial_days_left = max(0, (company.trial_ends_at.date() - now.date()).days)
    return {
        "company": {
            "id": str(company.id),
            "name": company.name,
            "code": company.code,
            "status": company_status,
            "trial_days_left": trial_days_left,
        },
        "summary": {
            "completed_today": completed_today,
            "overdue": overdue,
            "quality_exceptions": total_quality_exceptions,
            "open_issues": open_issues,
            "pending_review": pending_review,
        },
        "branches": branch_summaries,
    }


def _clone_task(instance: TaskInstance, reason: str) -> TaskInstance:
    return TaskInstance.objects.create(
        company=instance.company,
        branch=instance.branch,
        template=instance.template,
        template_version=instance.template_version,
        schedule=instance.schedule,
        scheduled_for=timezone.now(),
        due_at=timezone.now() + timedelta(hours=1),
        status=TaskStatus.PENDING,
        assigned_user=instance.assigned_user,
    )


@transaction.atomic
def create_review_decision(
    *,
    company: Company,
    user: User,
    decision_type: str,
    reason: str = "",
    task_instance_id: str | None = None,
    evidence_item_id: str | None = None,
    issue_report_id: str | None = None,
    restriction_name: str = "",
) -> ReviewDecision:
    task = None
    evidence = None
    issue = None
    branch = None
    original_status = ""
    resulting_status = ""
    generated_task = None

    if task_instance_id:
        task = TaskInstance.objects.select_for_update().get(id=task_instance_id, company=company)
        branch = task.branch
        original_status = str(task.status)
        resulting_status = str(task.status)
        if decision_type == ReviewDecisionType.CANCEL:
            task = cancel_task(str(task.id), user, reason)
            resulting_status = str(task.status)
        elif decision_type in {ReviewDecisionType.RETRY_SAME_TASK, ReviewDecisionType.CREATE_CORRECTIVE_TASK}:
            generated_task = _clone_task(task, reason)
        elif decision_type == ReviewDecisionType.MARK_MISSED and task.status not in {TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
            task.status = TaskStatus.OVERDUE
            task.overdue_at = task.overdue_at or timezone.now()
            task.save(update_fields=["status", "overdue_at", "updated_at"])
            resulting_status = str(task.status)
    elif evidence_item_id:
        evidence = EvidenceItem.objects.select_for_update().get(id=evidence_item_id, company=company)
        branch = evidence.branch
        original_status = str(evidence.status)
        resulting_status = str(evidence.status)
        if decision_type in {ReviewDecisionType.APPROVE, ReviewDecisionType.APPROVE_DESPITE_ALERT}:
            evidence.status = EvidenceStatus.SUBMITTED
            evidence.save(update_fields=["status", "updated_at"])
            resulting_status = str(evidence.status)
        elif decision_type == ReviewDecisionType.MARK_MISSED:
            evidence.status = EvidenceStatus.REJECTED
            evidence.save(update_fields=["status", "updated_at"])
            resulting_status = str(evidence.status)
    elif issue_report_id:
        issue = TaskIssueReport.objects.select_for_update().get(id=issue_report_id, company=company)
        branch = issue.branch
        original_status = "open" if issue.resolved_at is None else "resolved"
        resulting_status = original_status
        if decision_type in {ReviewDecisionType.APPROVE, ReviewDecisionType.APPROVE_DESPITE_ALERT}:
            issue.resolved_at = timezone.now()
            issue.resolution_note = reason
            issue.save(update_fields=["resolved_at", "resolution_note"])
            resulting_status = "resolved"

    if branch is None:
        raise ValueError("Review decision requires a task, evidence item, or issue report.")
    if str(branch.id) not in accessible_branch_ids(company, user):
        raise ValueError("User cannot review this branch.")

    decision = ReviewDecision.objects.create(
        company=company,
        branch=branch,
        decided_by=user,
        decision_type=decision_type,
        reason=reason,
        task_instance=task,
        evidence_item=evidence,
        issue_report=issue,
        generated_task_instance=generated_task,
        restriction_name=restriction_name,
        original_status=original_status,
        resulting_status=resulting_status,
        metadata={"generated_task_instance_id": str(generated_task.id) if generated_task else ""},
    )
    record_audit_event(
        event_type="REVIEW_DECISION_CREATED",
        target_type="review_decision",
        target_id=str(decision.id),
        actor_id=str(user.id),
        branch_id=str(branch.id),
        metadata={"decision_type": decision_type, "restriction_name": restriction_name},
    )
    from apps.ai_gateway.services import link_analysis_runs_to_review_decision

    link_analysis_runs_to_review_decision(decision)
    return decision
