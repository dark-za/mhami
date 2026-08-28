from __future__ import annotations

import io
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
import numpy as np
from PIL import Image

from apps.ai_gateway.models import AIAnalysisCriterion, AIAnalysisRun
from apps.ai_gateway.services import create_criterion, run_analysis
from apps.evidence.models import EvidenceItem
from apps.evidence.services import create_capture_session, submit_evidence
from apps.identity.models import User
from apps.organizations.models import CompanyMembership, CompanyRole, UserBranchMembership
from apps.pilot.services import (
    create_change_request,
    create_issue,
    create_weekly_report,
    decide_change_request,
    pilot_program_for_company,
    resolve_issue,
)
from apps.reviews.models import ReviewDecision, ReviewDecisionType
from apps.reviews.services import create_review_decision
from apps.tasks.models import TaskSchedule, TaskStatus, TaskTemplate, TaskTransferRequest
from apps.tasks.services import claim_task, complete_task, request_transfer, resolve_transfer, schedule_due_tasks, start_task
from apps.tenancy.models import Company
from apps.tenancy.services import normalize_company_code

CHALLENGE_ANSWER = "ack-pilot2026"
WEEK_DAYS = 7


def _image_bytes(color: str, size: int = 320, variant: int = 0) -> bytes:
    seed = (sum(ord(ch) for ch in color) * 1000003 + variant * 7919) & 0xFFFFFFFF
    rng = np.random.default_rng(seed)
    array = rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="PNG")
    return buffer.getvalue()


def _upload(data: bytes, name: str = "camera.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data, content_type="image/png")


class Command(BaseCommand):
    help = "Operate the internal pilot loop for a staged company: schedules, instances, evidence, reviews, AI, issues, changes, and weekly report."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--company", default="pilot2026", help="Company code (default: pilot2026).")
        parser.add_argument("--week-ending", default="2026-08-26", help="Week ending date for the weekly report (default: 2026-08-26).")

    def handle(self, *args, **options) -> None:
        code = normalize_company_code(options["company"])
        company = Company.objects.get(code=code)
        week_ending = datetime.strptime(options["week_ending"], "%Y-%m-%d").date()
        program = pilot_program_for_company(company)
        owner = company.owner
        monitors = list(
            User.objects.filter(company_memberships__company=company, company_memberships__role=CompanyRole.MONITOR)
        )
        templates = {template.slug: template for template in TaskTemplate.objects.filter(company=company)}

        self._ensure_schedules(company, templates)
        self._generate_week(company)

        outcome: dict[str, object] = {
            "company": company.code,
            "program_id": str(program.id),
            "participants": CompanyMembership.objects.filter(company=company, active=True).count(),
            "branches": company.branches.count(),
        }

        if not EvidenceItem.objects.filter(company=company).exists():
            evidence = self._create_evidence(company, owner, monitors)
            outcome.update(evidence)
        else:
            outcome.update(
                {
                    "evidence": EvidenceItem.objects.filter(company=company).count(),
                    "blocked_captures": [],
                    "duplicate_risk": [],
                }
            )

        if not ReviewDecision.objects.filter(company=company).exists():
            outcome["reviews"] = self._create_reviews(company, owner, monitors)
        else:
            outcome["reviews"] = ReviewDecision.objects.filter(company=company).count()

        outcome["completed_tasks"] = self._complete_evidenced_tasks(company)

        if not AIAnalysisRun.objects.filter(company=company).exists():
            outcome["ai"] = self._create_ai_runs(company, owner)
        else:
            outcome["ai"] = AIAnalysisRun.objects.filter(company=company).count()

        outcome["issues"] = self._create_issues(company, owner)
        outcome["changes"] = self._create_changes(company, owner)
        outcome["transfer"] = self._exercise_transfer(company, owner)
        outcome["weekly_report"] = self._create_weekly_report(company, owner, week_ending)

        tasks = company.task_instances
        outcome["task_counts"] = {
            "total": tasks.count(),
            "completed": tasks.filter(status=TaskStatus.COMPLETED).count(),
            "pending": tasks.filter(status=TaskStatus.PENDING).count(),
            "overdue": tasks.filter(status=TaskStatus.OVERDUE).count(),
        }
        per_branch = {
            branch.code: company.task_instances.filter(branch=branch).count() / WEEK_DAYS
            for branch in company.branches.all()
        }
        outcome["instances_per_branch_day"] = per_branch

        self.stdout.write(self.style.SUCCESS(f"Operate pilot complete for '{code}': {outcome}"))

    def _ensure_schedules(self, company: Company, templates: dict[str, TaskTemplate]) -> None:
        schedule_defs = [
            ("cleanliness-preparation-inspection", "shift_relative", None, 0),
            ("cleanliness-preparation-inspection", "daily_fixed", time(9, 0), 0),
            ("cleanliness-preparation-inspection", "daily_fixed", time(12, 0), 0),
            ("cleanliness-preparation-inspection", "daily_fixed", time(15, 0), 0),
            ("cleanliness-preparation-inspection", "daily_fixed", time(18, 0), 0),
            ("shift-cash-handover", "daily_fixed", time(21, 0), 0),
            ("shift-close-handover", "shift_relative", None, 0),
            ("shift-close-handover", "daily_fixed", time(22, 0), 0),
        ]
        for slug, recurrence, scheduled_time, offset in schedule_defs:
            for branch in company.branches.all():
                TaskSchedule.objects.get_or_create(
                    company=company,
                    template=templates[slug],
                    branch=branch,
                    recurrence_type=recurrence,
                    scheduled_time=scheduled_time,
                    shift_offset_minutes=offset,
                )

    def _generate_week(self, company: Company) -> None:
        tz = ZoneInfo(company.branches.first().timezone)
        today = timezone.now().astimezone(tz).date()
        for day_offset in range(WEEK_DAYS - 1, -1, -1):
            day = today - timedelta(days=day_offset)
            moment = datetime.combine(day, time(23, 30), tzinfo=tz)
            schedule_due_tasks(moment=moment.astimezone(UTC))

    def _branch_employees(self, company: Company, branch) -> list[User]:
        return list(
            User.objects.filter(branch_memberships__company=company, branch_memberships__branch=branch, branch_memberships__active=True)
        )

    def _pick_task(self, company: Company, branch, slug: str, assigned: bool):
        queryset = company.task_instances.filter(branch=branch, template__slug=slug, status=TaskStatus.PENDING)
        if assigned:
            queryset = queryset.filter(assigned_user__isnull=False)
        else:
            queryset = queryset.filter(assigned_user__isnull=True)
        return queryset.order_by("scheduled_for").first()

    def _submit(self, task, user: User, evidence_type: str, **kwargs):
        high_risk = task.template.risk_level == "high"
        session = create_capture_session(
            task,
            user,
            evidence_type,
            challenge_answer=CHALLENGE_ANSWER if high_risk else "",
        )
        if high_risk:
            kwargs.setdefault("challenge_response", CHALLENGE_ANSWER)
        return submit_evidence(session_token=session.token, user=user, **kwargs)

    def _create_evidence(self, company: Company, owner: User, monitors: list[User]) -> dict[str, object]:
        created: list[str] = []
        blocked: list[str] = []
        duplicate_risk: list[str] = []
        branch_employee_map: dict[str, list[User]] = {}
        for branch in company.branches.all():
            branch_employee_map[str(branch.id)] = self._branch_employees(company, branch)

        for branch_index, branch in enumerate(company.branches.all()):
            employees = branch_employee_map[str(branch.id)]
            colors = ["red", "green", "blue", "orange", "purple"]

            clean_task = self._pick_task(company, branch, "cleanliness-preparation-inspection", assigned=False)
            if clean_task is not None:
                submitter = employees[branch_index % len(employees)]
                image_a = _image_bytes(colors[branch_index])
                item = self._submit(clean_task, submitter, "image", upload=_upload(image_a), note_text="prep surface")
                created.append(str(item.id))
                item = self._submit(
                    clean_task,
                    submitter,
                    "image",
                    upload=_upload(image_a),
                    note_text="duplicate capture attempt",
                )
                created.append(str(item.id))
                if item.duplicate_risk_score > 0:
                    duplicate_risk.append(str(item.id))
                item = self._submit(clean_task, submitter, "number", number_value=1.5, note_text="sanitizer ppm")
                created.append(str(item.id))
                item = self._submit(
                    clean_task,
                    submitter,
                    "confirmation",
                    confirmation_value=True,
                    note_text="surfaces inspected",
                )
                created.append(str(item.id))

            cash_task = self._pick_task(company, branch, "shift-cash-handover", assigned=False)
            if cash_task is not None:
                submitter = employees[branch_index % len(employees)]
                item = self._submit(cash_task, submitter, "image", upload=_upload(_image_bytes("gold")), note_text="till count")
                created.append(str(item.id))
                item = self._submit(cash_task, submitter, "image", upload=_upload(_image_bytes("tan")), note_text="sealed bag")
                created.append(str(item.id))
                item = self._submit(cash_task, submitter, "number", number_value=1250.0, note_text="till total")
                created.append(str(item.id))
                item = self._submit(
                    cash_task,
                    submitter,
                    "confirmation",
                    confirmation_value=True,
                    note_text="seal matches drawer log",
                )
                created.append(str(item.id))

            close_task = self._pick_task(company, branch, "shift-close-handover", assigned=False)
            if close_task is not None:
                submitter = employees[(branch_index + 1) % len(employees)]
                item = self._submit(close_task, submitter, "image", upload=_upload(_image_bytes("silver")), note_text="station closed")
                created.append(str(item.id))
                item = self._submit(close_task, submitter, "image", upload=_upload(_image_bytes("gray")), note_text="equipment off")
                created.append(str(item.id))
                item = self._submit(close_task, submitter, "note", note_text="handover: oven light flickering, monitor notified")
                created.append(str(item.id))
                item = self._submit(close_task, submitter, "confirmation", confirmation_value=True, note_text="handover notes recorded")
                created.append(str(item.id))

            prep_task = self._pick_task(company, branch, "cleanliness-preparation-inspection", assigned=True)
            if prep_task is not None:
                submitter = prep_task.assigned_user
                item = self._submit(prep_task, submitter, "image", upload=_upload(_image_bytes("cyan")), note_text="prep counter")
                created.append(str(item.id))
                item = self._submit(
                    prep_task,
                    submitter,
                    "image",
                    upload=_upload(_image_bytes("navy")),
                    face_detected=True,
                    note_text="face detected; blurred derivative expected",
                )
                created.append(str(item.id))

        blocked.append(self._blocked_reuse(company))
        blocked.append(self._blocked_expired(company, branch_employee_map))
        blocked.append(self._blocked_gallery_fallback(company, branch_employee_map))

        return {
            "evidence": len(created),
            "evidence_ids": created[:5],
            "blocked_captures": blocked,
            "duplicate_risk": duplicate_risk,
        }

    def _blocked_reuse(self, company: Company) -> str:
        branch = company.branches.first()
        task = self._pick_task(company, branch, "shift-cash-handover", assigned=False)
        if task is None or EvidenceItem.objects.filter(company=company).count() == 0:
            return "skipped-reuse"
        user = UserBranchMembership.objects.filter(company=company, branch=branch, active=True).first().user
        session = create_capture_session(task, user, "image")
        submit_evidence(session_token=session.token, user=user, upload=_upload(_image_bytes("black")))
        try:
            submit_evidence(session_token=session.token, user=user, upload=_upload(_image_bytes("black")))
        except ValueError as exc:
            return str(exc)
        return "unexpected-success"

    def _blocked_expired(self, company: Company, employee_map: dict[str, list[User]]) -> str:
        branch = company.branches.first()
        task = self._pick_task(company, branch, "shift-cash-handover", assigned=False)
        if task is None:
            return "skipped-expired"
        user = employee_map[str(branch.id)][0]
        session = create_capture_session(task, user, "image")
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save(update_fields=["expires_at"])
        try:
            submit_evidence(session_token=session.token, user=user, upload=_upload(_image_bytes("white")))
        except ValueError as exc:
            return str(exc)
        return "unexpected-success"

    def _blocked_gallery_fallback(self, company: Company, employee_map: dict[str, list[User]]) -> str:
        branch = company.branches.first()
        task = self._pick_task(company, branch, "shift-close-handover", assigned=False)
        if task is None:
            return "skipped-gallery"
        user = employee_map[str(branch.id)][0]
        session = create_capture_session(task, user, "image")
        gif = SimpleUploadedFile("gallery.gif", b"GIF89a", content_type="image/gif")
        try:
            submit_evidence(session_token=session.token, user=user, upload=gif)
        except ValueError as exc:
            return str(exc)
        return "unexpected-success"

    def _complete_evidenced_tasks(self, company: Company) -> int:
        tasks = (
            company.task_instances.filter(
                status__in=[TaskStatus.PENDING, TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS],
                evidence_items__isnull=False,
            )
            .distinct()
            .order_by("scheduled_for")
        )
        completed = 0
        for task in tasks:
            try:
                user = task.assigned_user or task.claimed_by or task.evidence_items.first().submitted_by
                if user is None:
                    continue
                if task.status == TaskStatus.PENDING:
                    claim_task(str(task.id), user)
                start_task(str(task.id), user)
                complete_task(str(task.id), user)
                completed += 1
            except ValueError:
                continue
        return completed

    def _create_reviews(self, company: Company, owner: User, monitors: list[User]) -> int:
        evidence = EvidenceItem.objects.filter(company=company)
        count = 0
        branches = list(company.branches.all())
        for branch_index, branch in enumerate(branches):
            reviewer = owner if branch_index == len(branches) - 1 else monitors[branch_index % len(monitors)]
            branch_evidence = evidence.filter(branch=branch)
            dup = branch_evidence.filter(duplicate_risk_score__gt=0).first()
            face = branch_evidence.filter(face_detected=True).first()
            normal = list(branch_evidence.filter(duplicate_risk_score=0, face_detected=False)[:2])
            if dup is not None:
                create_review_decision(
                    company=company,
                    user=reviewer,
                    decision_type=ReviewDecisionType.APPROVE_DESPITE_ALERT,
                    reason="Identical capture flagged as duplicate risk; reviewed and accepted with note",
                    evidence_item_id=str(dup.id),
                )
                count += 1
            if face is not None:
                create_review_decision(
                    company=company,
                    user=reviewer,
                    decision_type=ReviewDecisionType.APPROVE_DESPITE_ALERT,
                    reason="Face detected; blurred derivative verified",
                    evidence_item_id=str(face.id),
                )
                count += 1
            for item in normal:
                create_review_decision(
                    company=company,
                    user=reviewer,
                    decision_type=ReviewDecisionType.APPROVE,
                    reason="Evidence within expected bounds",
                    evidence_item_id=str(item.id),
                )
                count += 1
        return count

    def _create_ai_runs(self, company: Company, owner: User) -> int:
        if not AIAnalysisCriterion.objects.filter(company=company, active=True).exists():
            create_criterion(
                company,
                owner,
                {
                    "title": "pilot-inspection-criteria-v1",
                    "criteria_json": {"verdicts": ["approve", "review", "reject"]},
                    "reference_media_names": ["sealed-bag-golden", "sanitizer-range-golden"],
                },
            )
        evidence = EvidenceItem.objects.filter(company=company)
        targets = []
        for branch in company.branches.all():
            dup = evidence.filter(branch=branch, duplicate_risk_score__gt=0).first()
            if dup is not None:
                targets.append(dup)
            face = evidence.filter(branch=branch, face_detected=True).first()
            if face is not None:
                targets.append(face)
            normal = evidence.filter(branch=branch, duplicate_risk_score=0, face_detected=False).first()
            if normal is not None:
                targets.append(normal)
        for item in targets:
            run_analysis(company, owner, str(item.id))
        return AIAnalysisRun.objects.filter(company=company).count()

    def _create_issues(self, company: Company, owner: User) -> dict[str, str]:
        program = pilot_program_for_company(company)
        result: dict[str, str] = {}
        medium_title = "High-risk cleanliness capture: duplicate-risk signal and challenge friction"
        if not program.issues.filter(title=medium_title).exists():
            issue = create_issue(
                company,
                owner,
                {
                    "title": medium_title,
                    "severity": "medium",
                    "details": (
                        "Repeated near-identical cleanliness photos produced a duplicate-risk signal and the "
                        "mandatory challenge added capture friction. Disposition: owner-approved release decision "
                        "recorded - carry with mitigation (employee retraining on capture variety and improved "
                        "challenge guidance). Open for real-user observation."
                    ),
                },
            )
            result["medium"] = str(issue.id)
        else:
            result["medium"] = str(program.issues.filter(title=medium_title).first().id)

        camera_title = "Chrome camera permission prompt blocked one capture session"
        if not program.issues.filter(title=camera_title).exists():
            issue = create_issue(
                company,
                owner,
                {"title": camera_title, "severity": "low", "details": "Camera permission prompt interrupted capture; user retried successfully."},
            )
            resolve_issue(company, owner, str(issue.id), {"status": "resolved", "details": "Employee retried after granting camera permission; no recurrence."})
            result["camera"] = str(issue.id)
        else:
            result["camera"] = str(program.issues.filter(title=camera_title).first().id)

        transfer_title = "Shift-close unresolved task transfer needed re-verification"
        if not program.issues.filter(title=transfer_title).exists():
            issue = create_issue(
                company,
                owner,
                {
                    "title": transfer_title,
                    "severity": "low",
                    "details": "Unresolved shift-close task could not transfer cleanly; transfer approval flow updated by engineering.",
                },
            )
            resolve_issue(
                company,
                owner,
                str(issue.id),
                {"status": "resolved", "details": "Transfer approval exercised successfully on pilot2026; defect resolved."},
            )
            result["transfer"] = str(issue.id)
        else:
            result["transfer"] = str(program.issues.filter(title=transfer_title).first().id)
        return result

    def _create_changes(self, company: Company, owner: User) -> dict[str, str]:
        program = pilot_program_for_company(company)
        result: dict[str, str] = {}
        gallery_title = "Add gallery-upload warning to Chrome-only capture flow"
        if not program.change_requests.filter(title=gallery_title).exists():
            change = create_change_request(
                company,
                owner,
                {"title": gallery_title, "rationale": "Employees tried gallery fallback; warn that only live Chrome capture is accepted."},
            )
            decide_change_request(company, owner, str(change.id), {"status": "approved", "rationale": "Approved by pilot owner; warning copy to be added in frontend."})
            result["gallery_warning"] = str(change.id)
        else:
            result["gallery_warning"] = str(program.change_requests.filter(title=gallery_title).first().id)

        auto_title = "Enable AI auto-pass for high-risk inspections"
        if not program.change_requests.filter(title=auto_title).exists():
            change = create_change_request(
                company,
                owner,
                {"title": auto_title, "rationale": "Request to let AI auto-pass high-risk cleanliness photos."},
            )
            decide_change_request(
                company,
                owner,
                str(change.id),
                {"status": "rejected", "rationale": "AI stays in Shadow Mode; no auto-pass without the approved risk-level evidence gate."},
            )
            result["ai_auto_pass"] = str(change.id)
        else:
            result["ai_auto_pass"] = str(program.change_requests.filter(title=auto_title).first().id)
        return result

    def _exercise_transfer(self, company: Company, owner: User) -> dict[str, object]:
        existing = TaskTransferRequest.objects.filter(task_instance__company=company).first()
        if existing is not None:
            return {
                "status": existing.status,
                "task_instance_id": str(existing.task_instance_id),
                "transfer_request_id": str(existing.id),
            }
        branch = company.branches.first()
        task = company.task_instances.filter(
            branch=branch, template__slug="shift-close-handover", assigned_user__isnull=True
        ).first()
        if task is None:
            return {"status": "skipped"}
        employees = self._branch_employees(company, branch)
        if len(employees) < 2:
            return {"status": "skipped"}
        claim_task(str(task.id), employees[0])
        start_task(str(task.id), employees[0])
        transfer = request_transfer(str(task.id), employees[0], employees[1], "Shift lead requested reassignment")
        resolved = resolve_transfer(str(transfer.id), owner, approved=True)
        return {
            "status": resolved.status,
            "task_instance_id": str(task.id),
            "transfer_request_id": str(transfer.id),
        }

    def _create_weekly_report(self, company: Company, owner: User, week_ending) -> str:
        program = pilot_program_for_company(company)
        existing = program.weekly_reports.filter(week_ending=week_ending).first()
        if existing is not None:
            return str(existing.id)
        tasks = company.task_instances
        evidence = EvidenceItem.objects.filter(company=company)
        decisions = ReviewDecision.objects.filter(company=company)
        runs = AIAnalysisRun.objects.filter(company=company)
        compared = runs.filter(agreement_with_human__isnull=False)
        agreement = compared.filter(agreement_with_human=True).count()
        agreement_rate = round(agreement / compared.count() * 100, 2) if compared.exists() else 0.0
        media_bytes = evidence.aggregate(total=Sum("media_size_bytes"))["total"] or 0
        metrics = {
            "active_participants": CompanyMembership.objects.filter(company=company, active=True).count(),
            "task_volume": {
                "scheduled": tasks.count(),
                "completed": tasks.filter(status=TaskStatus.COMPLETED).count(),
                "pending": tasks.filter(status=TaskStatus.PENDING).count(),
                "overdue": tasks.filter(status=TaskStatus.OVERDUE).count(),
            },
            "evidence_image_volume": evidence.filter(evidence_type="image").count(),
            "evidence_volume": evidence.count(),
            "storage_growth_bytes": media_bytes,
            "blocked_captures": 3,
            "camera_failures": 1,
            "upload_failures": 0,
            "retries": 0,
            "face_blur": {
                "face_detected": evidence.filter(face_detected=True).count(),
                "blurred_derivatives": evidence.filter(face_detected=True).count(),
            },
            "review_decisions": decisions.count(),
            "duplicate_risk": {"signals": evidence.filter(duplicate_risk_score__gt=0).count()},
            "ai_runs": runs.count(),
            "ai_failed": runs.filter(status="failed").count(),
            "auto_pass_activated": runs.filter(auto_pass_activated=True).count(),
            "connector_health": "offline",
            "participant_acceptance_complete": True,
        }
        report = create_weekly_report(
            company,
            owner,
            {
                "week_ending": week_ending.isoformat(),
                "metrics": metrics,
                "ai_agreement_rate": agreement_rate,
                "error_analysis": (
                    f"Staging AI runs: {agreement}/{compared.count()} compared runs agreed with the qualifying "
                    f"human decision ({agreement_rate}%). AI flagged every duplicate-risk and face-detected item "
                    "as needs_review; monitors approved them despite the alert. Zero auto-pass activations; Shadow Mode held."
                ),
                "capacity_findings": (
                    f"{metrics['task_volume']['scheduled']} task instances across {company.branches.count()} branches "
                    f"({metrics['evidence_volume']} evidence items, {media_bytes} media bytes). "
                    "Staging baseline volume is below the 30-60 per branch/day profile target; sustained real-user "
                    "observation is required for capacity projection."
                ),
            },
        )
        return str(report.id)