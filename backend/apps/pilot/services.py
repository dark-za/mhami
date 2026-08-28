from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.ai_gateway.models import AIAnalysisRun
from apps.audit.services import record_audit_event
from apps.backups.models import BackupRun, BackupStatus
from apps.connector_control.models import TenantConnectorEnrollment
from apps.evidence.models import EvidenceItem
from apps.exports.models import ExportRequest, ExportStatus
from apps.identity.models import User
from apps.platform_core.errors import PlatformAPIException
from apps.platform_core.service_base import audited_service
from apps.reviews.models import ReviewDecision
from apps.tenancy.models import Company

from .models import PilotChangeRequest, PilotCharter, PilotIssue, PilotProgram, PilotWeeklyReport


def pilot_program_for_company(company: Company) -> PilotProgram:
    program, _created = PilotProgram.objects.get_or_create(
        company=company,
        defaults={
            "success_measures": [
                "Employees complete Chrome-only tasks",
                "Monitors resolve exceptions without engineering intervention",
                "Owners see weekly branch and quality trends",
            ],
            "escalation_contacts": [],
            "operating_checklist": [
                "Pilot backup restore passes",
                "Security review complete",
                "Staging release candidate validated",
            ],
            "weekly_metrics_goal": {"branches": 3, "employees": 30},
        },
    )
    return program


def pilot_dashboard(company: Company, user: User) -> dict[str, object]:
    program = pilot_program_for_company(company)
    now = timezone.now()
    week_start = now - timedelta(days=7)
    evidence = EvidenceItem.objects.filter(company=company, created_at__gte=week_start)
    ai_runs = AIAnalysisRun.objects.filter(company=company, created_at__gte=week_start)
    connector = TenantConnectorEnrollment.objects.filter(company=company).first()
    backup = BackupRun.objects.filter(company=company).order_by("-started_at").first()
    return {
        "program": {
            "id": str(program.id),
            "company": str(program.company_id),
            "status": program.status,
            "branch_count_target": program.branch_count_target,
            "employee_count_target": program.employee_count_target,
            "chrome_device_count": program.chrome_device_count,
            "ai_provider_name": program.ai_provider_name,
            "connector_owner": program.connector_owner,
            "test_environment": program.test_environment,
            "success_measures": program.success_measures,
            "escalation_contacts": program.escalation_contacts,
            "operating_checklist": program.operating_checklist,
            "weekly_metrics_goal": program.weekly_metrics_goal,
            "notes": program.notes,
        },
        "summary": {
            "evidence_items_week": evidence.count(),
            "image_evidence_week": evidence.filter(evidence_type="image").count(),
            "face_blurred_week": evidence.filter(face_detected=True).count(),
            "ai_runs_week": ai_runs.count(),
            "ai_agreement_rate": _ai_agreement_rate(ai_runs),
            "backup_completed": bool(backup and backup.status == BackupStatus.COMPLETED),
            "connector_status": connector.status if connector else "offline",
            "connector_health": connector.health_status if connector else "offline",
            "exports_completed": ExportRequest.objects.filter(company=company, status=ExportStatus.COMPLETED).count(),
            "reviews_created": ReviewDecision.objects.filter(company=company, created_at__gte=week_start).count(),
        },
        "counts": {
            "issues": PilotIssue.objects.filter(pilot_program=program).count(),
            "change_requests": PilotChangeRequest.objects.filter(pilot_program=program).count(),
            "reports": PilotWeeklyReport.objects.filter(pilot_program=program).count(),
        },
        "charter": charter_payload(company),
        "program_id": str(program.id),
    }


def charter_payload(company: Company) -> dict[str, object] | None:
    """Return the latest signed charter for ``company`` or ``None``."""
    charter = latest_charter(company)
    if charter is None:
        return None


@transaction.atomic
def sign_charter(company: Company, user: User, payload: dict[str, object]) -> PilotCharter:
    """PILOT-01: sign a pilot charter for ``company``.

    The charter is HMAC-signed over the canonical payload. The audit event
    is recorded by the caller (the API view) to keep the event_type
    explicit at the HTTP layer.
    """
    program = pilot_program_for_company(company)
    charter = PilotCharter.objects.create(
        pilot_program=program,
        company=company,
        decision=payload["decision"],
        rationale=payload["rationale"],
        conditions=payload.get("conditions", ""),
        observation_start=payload.get("observation_start"),
        observation_end=payload.get("observation_end"),
        success_measures=payload.get("success_measures") or [],
        signed_by=user,
        metadata=payload.get("metadata") or {},
    )
    charter.signature_hmac = charter.compute_signature()
    charter.save(update_fields=["signature_hmac"])
    return charter


def has_signed_charter(company: Company) -> bool:
    """PILOT-01: True if the company has at least one ``authorize`` charter."""
    return PilotCharter.objects.filter(
        company=company, decision=PilotCharter.Decision.AUTHORIZE
    ).exists()
    return {
        "id": str(charter.id),
        "pilot_program": str(charter.pilot_program_id),
        "decision": charter.decision,
        "rationale": charter.rationale,
        "conditions": charter.conditions,
        "observation_start": charter.observation_start.isoformat() if charter.observation_start else None,
        "observation_end": charter.observation_end.isoformat() if charter.observation_end else None,
        "success_measures": list(charter.success_measures or []),
        "signed_by": str(charter.signed_by_id),
        "signed_at": charter.signed_at.isoformat() if charter.signed_at else None,
        "signature_valid": charter.verify_signature(),
    }


def latest_charter(company: Company) -> PilotCharter | None:
    return (
        PilotCharter.objects.filter(company=company)
        .select_related("signed_by")
        .order_by("-signed_at")
        .first()
    )


def _ai_agreement_rate(ai_runs) -> Decimal:
    total = ai_runs.count()
    if total == 0:
        return Decimal("0.00")
    agree = ai_runs.filter(agreement_with_human=True).count()
    return (Decimal(agree) / Decimal(total)) * Decimal(100)


@transaction.atomic
def update_program(company: Company, user: User, payload: dict[str, object]) -> PilotProgram:
    program = pilot_program_for_company(company)
    for field, value in payload.items():
        setattr(program, field, value)
    program.updated_by = user
    program.save()
    record_audit_event(
        event_type="PILOT_PROGRAM_UPDATED",
        target_type="pilot_program",
        target_id=str(program.id),
        actor_id=str(user.id),
        branch_id="",
        metadata=payload,
    )
    return program


@audited_service(event_type="PILOT_WEEKLY_REPORT_CREATED", target_type="pilot_weekly_report")
def create_weekly_report(company: Company, user: User, payload: dict[str, object]) -> PilotWeeklyReport:
    program = pilot_program_for_company(company)
    report = PilotWeeklyReport.objects.create(
        pilot_program=program,
        week_ending=payload["week_ending"],
        metrics=payload.get("metrics", {}),
        ai_agreement_rate=payload.get("ai_agreement_rate", _ai_agreement_rate(AIAnalysisRun.objects.filter(company=company))),
        error_analysis=payload.get("error_analysis", ""),
        capacity_findings=payload.get("capacity_findings", ""),
        created_by=user,
    )
    return report


@transaction.atomic
def create_issue(company: Company, user: User, payload: dict[str, object]) -> PilotIssue:
    program = pilot_program_for_company(company)
    issue = PilotIssue.objects.create(pilot_program=program, title=payload["title"], severity=payload.get("severity", "medium"), details=payload.get("details", ""), created_by=user)
    record_audit_event(
        event_type="PILOT_ISSUE_CREATED",
        target_type="pilot_issue",
        target_id=str(issue.id),
        actor_id=str(user.id),
        branch_id="",
        metadata={"severity": issue.severity},
    )
    return issue


@transaction.atomic
def create_change_request(company: Company, user: User, payload: dict[str, object]) -> PilotChangeRequest:
    program = pilot_program_for_company(company)
    change = PilotChangeRequest.objects.create(pilot_program=program, title=payload["title"], rationale=payload.get("rationale", ""), created_by=user)
    record_audit_event(
        event_type="PILOT_CHANGE_REQUESTED",
        target_type="pilot_change_request",
        target_id=str(change.id),
        actor_id=str(user.id),
        branch_id="",
        metadata={"title": change.title},
    )
    return change


@transaction.atomic
def resolve_issue(company: Company, user: User, issue_id: str, payload: dict[str, object]) -> PilotIssue:
    program = pilot_program_for_company(company)
    issue = PilotIssue.objects.filter(pilot_program=program, id=issue_id).first()
    if issue is None:
        raise PlatformAPIException("Pilot issue not found.")
    if "status" in payload:
        issue.status = payload["status"]
    if "details" in payload:
        issue.details = payload["details"]
    issue.save(update_fields=[f for f in ("status", "details") if f in payload])
    record_audit_event(
        event_type="PILOT_ISSUE_RESOLVED",
        target_type="pilot_issue",
        target_id=str(issue.id),
        actor_id=str(user.id),
        branch_id="",
        metadata={"status": issue.status},
    )
    return issue


@transaction.atomic
def decide_change_request(company: Company, user: User, change_id: str, payload: dict[str, object]) -> PilotChangeRequest:
    program = pilot_program_for_company(company)
    change = PilotChangeRequest.objects.filter(pilot_program=program, id=change_id).first()
    if change is None:
        raise PlatformAPIException("Pilot change request not found.")
    if "status" in payload:
        change.status = payload["status"]
    if "rationale" in payload:
        change.rationale = payload["rationale"]
    if change.status in {"approved", "rejected"}:
        change.approved_by = user
    change.save(update_fields=[f for f in ("status", "rationale", "approved_by") if f in payload or change.status in {"approved", "rejected"}])
    record_audit_event(
        event_type="PILOT_CHANGE_DECIDED",
        target_type="pilot_change_request",
        target_id=str(change.id),
        actor_id=str(user.id),
        branch_id="",
        metadata={"status": change.status},
    )
    return change
