from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import time, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.test import Client
from django.utils import timezone
from PIL import Image

import numpy as np

from apps.ai_gateway.services import run_analysis
from apps.audit.models import AuditEvent
from apps.backups.services import _validated_archive, backup_storage_root, create_backup_run, download_backup_artifact, restore_backup_run
from apps.connector_control.models import ConnectorHealthStatus
from apps.connector_control.services import current_connector_health, enroll_connector, observe_connector_health
from apps.evidence.models import EvidenceItem
from apps.evidence.services import can_access_media, create_capture_session, submit_evidence
from apps.exports.services import create_export_request, export_download_response, prepare_export_request
from apps.identity.models import User
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.organizations.models import Branch, CompanyMembership, CompanyRole, JobRole, UserBranchMembership
from apps.tasks.models import TaskAssignmentMode, TaskInstance, TaskSchedule, TaskTemplate, TaskTemplateVersion
from apps.tasks.services import schedule_due_tasks
from apps.tenancy.auth_backends import CompanyCodeBackend
from apps.tenancy.models import Company, LegalAcceptance, LegalDocumentType, SupportAuthorization
from apps.tenancy.services import (
    enroll_totp,
    ensure_company_operational,
    grant_support,
    process_lifecycle_expirations,
    register_company,
    revoke_support,
)

PROBE_CODE = "lifecycleprobe"
PASSWORD = "PilotPass!2026"


def _image_bytes(color: str, size: int = 320) -> bytes:
    seed = (sum(ord(ch) for ch in color) * 1000003 + 31) & 0xFFFFFFFF
    rng = np.random.default_rng(seed)
    array = rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="PNG")
    return buffer.getvalue()


def _upload(data: bytes, name: str = "camera.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data, content_type="image/png")


class Command(BaseCommand):
    help = "Run the Phase 12 resilience and authorization exercises against a disposable company and pilot2026."

    def handle(self, *args, **options) -> None:
        result: dict[str, object] = {}
        probe = self._create_probe()
        result["probe_company_id"] = str(probe.id)
        result["tenant_isolation"] = self._tenant_isolation(probe)
        result["support_authorization"] = self._support_authorization(probe)
        result["lifecycle"] = self._lifecycle_probe(probe)
        pilot = Company.objects.get(code="pilot2026")
        result["backup_restore"] = self._backup_restore(pilot)
        result["connector"] = self._connector_outage(pilot)
        result["ai_failure"] = self._ai_failure(pilot)
        result["export"] = self._export_probe(pilot)
        self.stdout.write(self.style.SUCCESS(json.dumps(result, indent=2, default=str)))

    def _create_probe(self) -> Company:
        existing = Company.objects.filter(code=PROBE_CODE).first()
        if existing is not None:
            self._teardown_probe(existing)
        company, owner = register_company(
            company_name="Lifecycle Probe Co",
            company_code=PROBE_CODE,
            industry="other",
            owner_login_id=f"{PROBE_CODE}-owner",
            owner_password=PASSWORD,
            owner_display_name="Probe Owner",
        )
        for document_type in (
            LegalDocumentType.TERMS,
            LegalDocumentType.PRIVACY,
            LegalDocumentType.AI_TRANSFER,
            LegalDocumentType.EMPLOYEE_PRIVACY,
        ):
            LegalAcceptance.objects.create(company=company, accepted_by=owner, document_type=document_type, document_version="v1")
        staff_role = JobRole.objects.create(company=company, name="Staff", code="staff")
        branch = Branch.objects.create(
            company=company,
            name="Probe Branch",
            code=f"{PROBE_CODE}-b1",
            timezone="UTC",
            operational_day_cutoff=time(6, 0),
        )
        employee = User.objects.create_user(login_id=f"{PROBE_CODE}-emp1", password=PASSWORD, display_name="Probe Employee")
        CompanyMembership.objects.create(company=company, user=employee, role=CompanyRole.EMPLOYEE)
        UserBranchMembership.objects.create(company=company, user=employee, branch=branch, job_role=staff_role)
        self._probe_evidence(company, branch, employee)
        return company

    def _teardown_probe(self, company: Company) -> None:
        from apps.ai_gateway.models import AIAnalysisCriterion, AIAnalysisRun, AIProviderConfig
        from apps.backups.models import BackupPolicy, BackupRun, RestoreRun
        from apps.connector_control.models import TenantConnectorEnrollment
        from apps.evidence.models import CaptureSession, EvidenceItem, TaskDiscussionMessage, TaskIssueReport
        from apps.exports.models import ExportBoundaryPolicy, ExportRequest
        from apps.notifications.models import Notification
        from apps.organizations.models import Branch, CompanyMembership, JobRole, UserBranchMembership, WeeklyShift
        from apps.pilot.models import PilotChangeRequest, PilotIssue, PilotProgram, PilotWeeklyReport
        from apps.reviews.models import ReviewDecision, ReviewPolicySetting
        from apps.tasks.models import TaskInstance, TaskSchedule, TaskTemplate, TaskTemplateVersion, TaskTransferRequest

        company_models = (
            AIAnalysisRun,
            ReviewDecision,
            EvidenceItem,
            CaptureSession,
            TaskIssueReport,
            TaskDiscussionMessage,
            TaskInstance,
            TaskSchedule,
            TaskTemplate,
            WeeklyShift,
            UserBranchMembership,
            JobRole,
            Branch,
            ExportRequest,
            BackupRun,
            RestoreRun,
            ExportBoundaryPolicy,
            BackupPolicy,
            ReviewPolicySetting,
            AIProviderConfig,
            AIAnalysisCriterion,
            SupportAuthorization,
            LegalAcceptance,
            CompanyMembership,
            Notification,
            PilotProgram,
        )
        for model in company_models:
            model.objects.filter(company=company).delete()
        TaskTransferRequest.objects.filter(task_instance__company=company).delete()
        TaskTemplateVersion.objects.filter(template__company=company).delete()
        TenantConnectorEnrollment.objects.filter(company=company).delete()
        for model in (PilotWeeklyReport, PilotIssue, PilotChangeRequest):
            model.objects.filter(pilot_program__company=company).delete()
        user_ids = list(company.memberships.values_list("user_id", flat=True))
        company.delete()
        probe_users = User.objects.filter(login_id__startswith=f"{PROBE_CODE}-")
        user_ids.extend(probe_users.values_list("id", flat=True))
        probe_users.delete()

    def _probe_evidence(self, company: Company, branch: Branch, employee: User) -> EvidenceItem:
        template = TaskTemplate.objects.create(
            company=company,
            branch=branch,
            slug="probe-clean",
            name="Probe clean",
            assignment_mode=TaskAssignmentMode.NAMED_USER,
            assigned_user=employee,
            risk_level="low",
        )
        TaskTemplateVersion.objects.create(
            template=template,
            version_number=1,
            instructions="Do work",
            checklist_definition=[],
            evidence_requirements=[{"type": "image"}],
        )
        TaskSchedule.objects.create(
            company=company,
            branch=branch,
            template=template,
            recurrence_type="daily_fixed",
            scheduled_time=time(9, 0),
        )
        instance = schedule_due_tasks(moment=timezone.now())[0]
        session = create_capture_session(instance, employee, "image")
        return submit_evidence(session_token=session.token, user=employee, upload=_upload(_image_bytes("probe")))

    def _tenant_isolation(self, probe: Company) -> dict[str, object]:
        pilot = Company.objects.get(code="pilot2026")
        pilot_evidence = EvidenceItem.objects.filter(company=pilot).first()
        probe_evidence = EvidenceItem.objects.filter(company=probe).first()
        probe_employee = User.objects.filter(login_id=f"{PROBE_CODE}-emp1").first()
        pilot_employee = User.objects.filter(login_id="pilot2026-emp1-1").first()
        media_cross_denied = not can_access_media(probe_employee, pilot_evidence) and not can_access_media(pilot_employee, probe_evidence)
        cross_lookup_denied = False
        try:
            EvidenceItem.objects.get(id=pilot_evidence.id, company=probe)
        except EvidenceItem.DoesNotExist:
            cross_lookup_denied = True
        export_cross_denied = False
        try:
            prepare_export_request(
                company=probe,
                user=probe_employee,
                export_type="csv",
                branch_ids=[str(pilot.branches.first().id)],
                categories=[],
            )
        except ValueError:
            export_cross_denied = True
        return {
            "cross_company_media_denied": media_cross_denied,
            "cross_company_lookup_denied": cross_lookup_denied,
            "cross_company_export_denied": export_cross_denied,
            "evidence_ids": {"pilot2026": str(pilot_evidence.id), "lifecycleprobe": str(probe_evidence.id)},
        }

    def _support_authorization(self, probe: Company) -> dict[str, object]:
        from apps.tenancy.api.views import _totp_token

        owner = probe.owner
        support = User.objects.create_user(login_id=f"{PROBE_CODE}-support", password=PASSWORD, display_name="Probe Support")
        grant = grant_support(probe, support, owner, reason="Staging support boundary exercise", expires_at=timezone.now() + timedelta(hours=1))
        enrollment = enroll_totp(support, label="support-totp")
        enrollment.verify()
        client = Client()
        client.defaults.setdefault("HTTP_HOST", "127.0.0.1")
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "company_code": PROBE_CODE,
                "login_id": support.login_id,
                "password": PASSWORD,
                "mfa_code": _totp_token(enrollment.secret),
            },
            content_type="application/json",
        )
        support_used = login_response.status_code == 200
        create_notification(
            company=probe,
            user=owner,
            notification_type="support.access.granted",
            title="Temporary support access granted",
            body="Support boundary exercise grant is active for lifecycleprobe.",
            severity="info",
            metadata={"support_user_id": str(support.id), "grant_id": str(grant.id)},
        )
        support_export = None
        if support_used:
            support_export = create_export_request(
                company=probe,
                user=support,
                export_type="csv",
                branch_ids=[str(branch.id) for branch in probe.branches.all()],
                categories=["evidence"],
            )
        revoke_support(grant, revoked_by=owner)
        post_revoke_login = CompanyCodeBackend().authenticate(
            None,
            company_code=PROBE_CODE,
            login_id=support.login_id,
            password=PASSWORD,
        )
        evidence = EvidenceItem.objects.filter(company=probe).first()
        return {
            "grant_id": str(grant.id),
            "totp_enrollment_id": str(enrollment.id),
            "support_login_allowed": support_used,
            "support_export_id": str(support_export.id) if support_export else None,
            "owner_notified": True,
            "post_revoke_login_denied": post_revoke_login is None,
            "post_revoke_media_denied": not can_access_media(support, evidence),
            "audit_events": {
                "granted": AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_GRANTED", target_id=str(grant.id)).exists(),
                "revoked": AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_REVOKED", target_id=str(grant.id)).exists(),
                "login": AuditEvent.objects.filter(event_type="USER_LOGIN", target_id=str(support.id)).exists(),
                "used": AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_USED", target_id=str(grant.id)).exists(),
            },
        }

    def _lifecycle_probe(self, probe: Company) -> dict[str, object]:
        dry_run = process_lifecycle_expirations(dry_run=True)
        probe.trial_ends_at = timezone.now() - timedelta(minutes=1)
        probe.save(update_fields=["trial_ends_at"])
        applied = process_lifecycle_expirations()
        probe.refresh_from_db()
        owner = probe.owner
        client = Client()
        client.defaults.setdefault("HTTP_HOST", "127.0.0.1")
        client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
        client.session["company_id"] = str(probe.id)
        client.session.save()
        mutation_response = client.post(
            "/api/v1/organizations/branches",
            data={"name": "Blocked", "code": "blocked", "timezone": "UTC", "operational_day_cutoff": "06:00"},
            content_type="application/json",
        )
        member_response = client.post(
            "/api/v1/auth/company/users",
            data={"login_id": "blocked-user", "password": "Password!123", "display_name": "Blocked"},
            content_type="application/json",
        )
        read_response = client.get("/api/v1/organizations/branches")
        export_works = bool(
            create_export_request(
                company=probe,
                user=owner,
                export_type="csv",
                branch_ids=[str(branch.id) for branch in probe.branches.all()],
                categories=["tasks"],
            )
        )
        operational_guard = False
        try:
            ensure_company_operational(probe)
        except ValueError:
            operational_guard = True
        return {
            "dry_run_counts": dry_run,
            "applied_counts": applied,
            "status": probe.status,
            "read_only_until": probe.read_only_until.isoformat(),
            "deletion_due_at": probe.deletion_due_at.isoformat() if probe.deletion_due_at else None,
            "mutation_branch_denied": mutation_response.status_code == 400,
            "mutation_member_denied": member_response.status_code == 400,
            "reads_work": read_response.status_code == 200,
            "export_works_read_only": export_works,
            "operational_guard_blocks": operational_guard,
            "lifecycle_audit": AuditEvent.objects.filter(event_type="COMPANY_LIFECYCLE_TRANSITIONED", target_id=str(probe.id)).exists(),
        }

    def _backup_restore(self, pilot: Company) -> dict[str, object]:
        owner = pilot.owner
        create_notification(
            company=pilot,
            user=owner,
            notification_type="backup.completed",
            title="Backup completed",
            body="Pre-restore exercise notification.",
            severity="success",
        )
        notification_backup = create_backup_run(pilot, owner)
        notification_restore_failed = False
        try:
            restore_backup_run(
                pilot,
                owner,
                str(notification_backup.id),
                f"pilot2026restore-{str(notification_backup.id)[:8]}",
                f"RESTORE {notification_backup.id}",
            )
        except ValueError:
            notification_restore_failed = True
        Notification.objects.filter(company=pilot).delete()
        backup = create_backup_run(pilot, owner)
        artifact = download_backup_artifact(pilot, str(backup.id))
        restore = restore_backup_run(
            pilot,
            owner,
            str(backup.id),
            f"pilot2026restore-{str(backup.id)[:8]}",
            f"RESTORE {backup.id}",
        )
        tamper_path = backup_storage_root() / "tampered-backup.zip"
        data = bytearray(artifact.read_bytes())
        data[len(data) // 2] ^= 0x01
        tamper_path.write_bytes(bytes(data))
        tamper_rejected = False
        try:
            _validated_archive(backup, tamper_path)
        except ValueError:
            tamper_rejected = True
        finally:
            tamper_path.unlink(missing_ok=True)
        manifest = backup.manifest
        return {
            "notification_restore_defect_reproduced": notification_restore_failed,
            "notification_backup_run_id": str(notification_backup.id),
            "backup_run_id": str(backup.id),
            "backup_status": backup.status,
            "artifact_name": backup.artifact_name,
            "artifact_sha256": backup.artifact_sha256,
            "restore_id": str(restore.id),
            "restore_status": restore.status,
            "target_name": restore.target_name,
            "verified_database": restore.verified_database,
            "verified_media": restore.verified_media,
            "verified_configuration": restore.verified_configuration,
            "manifest_counts": manifest.get("counts", {}),
            "restored_counts": restore.report.get("restored_counts", {}),
            "tamper_rejected": tamper_rejected,
        }

    def _connector_outage(self, pilot: Company) -> dict[str, object]:
        owner = pilot.owner
        fingerprint = hashlib.sha256(b"secret").hexdigest()
        enrollment = enroll_connector(pilot, owner, "0.1.0", fingerprint)
        observe_connector_health(str(enrollment.id), "0.1.0", "secret", ConnectorHealthStatus.HEALTHY)
        healthy = current_connector_health(enrollment).health_status
        enrollment.health_expires_at = timezone.now() - timedelta(seconds=1)
        enrollment.save(update_fields=["health_expires_at"])
        offline = current_connector_health(enrollment).health_status
        evidence = self._submit_during_outage(pilot)
        return {
            "enrollment_id": str(enrollment.id),
            "health_observed": healthy,
            "health_after_ttl_expiry": offline,
            "evidence_submitted_while_offline": evidence is not None,
            "evidence_id": str(evidence.id) if evidence else None,
        }

    def _submit_during_outage(self, pilot: Company) -> EvidenceItem | None:
        branch = pilot.branches.first()
        task = TaskInstance.objects.filter(company=pilot, branch=branch, status="pending").first()
        if task is None:
            return None
        user = task.assigned_user or task.template.company.owner
        session = create_capture_session(task, user, "image")
        return submit_evidence(session_token=session.token, user=user, upload=_upload(_image_bytes("outage")))

    def _ai_failure(self, pilot: Company) -> dict[str, object]:
        from apps.ai_gateway import services as ai_services

        evidence = EvidenceItem.objects.filter(company=pilot).first()
        original = ai_services._provider_for

        class _FailingProvider:
            def analyze(self, **kwargs):
                raise RuntimeError("simulated provider outage")

        def _failing_provider(config):
            return _FailingProvider()

        ai_services._provider_for = _failing_provider
        try:
            run = run_analysis(pilot, pilot.owner, str(evidence.id))
        finally:
            ai_services._provider_for = original
        evidence_after = self._submit_during_outage(pilot)
        return {
            "failed_run_id": str(run.id),
            "failed_run_status": run.status,
            "shadow_mode": run.shadow_mode,
            "auto_pass_activated": run.auto_pass_activated,
            "evidence_submitted_while_ai_failed": evidence_after is not None,
        }

    def _export_probe(self, pilot: Company) -> dict[str, object]:
        owner = pilot.owner
        branch = pilot.branches.first()
        export = create_export_request(
            company=pilot,
            user=owner,
            export_type="csv",
            branch_ids=[str(branch.id)],
            categories=["tasks", "evidence"],
        )
        response = export_download_response(pilot, owner, export.download_token)
        payload = b"".join(response.streaming_content)
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        task_branches = {row["branch"] for row in reader if row.get("kind") == "task"}
        scoped = bool(task_branches) and task_branches == {branch.name}
        cross_branch_denied = False
        employee = User.objects.filter(login_id="pilot2026-emp1-1").first()
        try:
            prepare_export_request(
                company=pilot,
                user=employee,
                export_type="csv",
                branch_ids=[str(pilot.branches.last().id)],
                categories=[],
            )
        except ValueError:
            cross_branch_denied = True
        return {
            "export_id": str(export.id),
            "download_token": export.download_token,
            "status": export.status,
            "requested_branch": branch.code,
            "rows_scoped_to_requested_branch": scoped,
            "task_row_branches": sorted(task_branches),
            "employee_cross_branch_denied": cross_branch_denied,
        }
