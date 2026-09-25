from __future__ import annotations

import csv
import hashlib
import io
import secrets
import zipfile
from datetime import timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.evidence.models import EvidenceItem
from apps.identity.models import User
from apps.notifications.services import emit_for_outbox_event
from apps.platform_core.outbox import emit_audit_and_outbox, quick_event
from apps.tasks.models import TaskInstance
from apps.tenancy.access import accessible_company_branch_ids
from apps.tenancy.models import Company

from .models import ExportBoundaryPolicy, ExportRequest, ExportStatus, ExportType


def export_storage_root() -> Path:
    root = Path(settings.MEDIA_ROOT) / "exports"
    root.mkdir(parents=True, exist_ok=True)
    return root


def accessible_branch_ids(company: Company, user: User) -> list[str]:
    """Resolve export scope from the user's role and branch assignments only."""
    return accessible_company_branch_ids(company, user)


def export_policy_for_company(company: Company) -> ExportBoundaryPolicy:
    policy, _created = ExportBoundaryPolicy.objects.get_or_create(company=company)
    return policy


def _ensure_authorized(company: Company, user: User, branch_ids: list[str]) -> None:
    allowed = set(accessible_branch_ids(company, user))
    if not set(branch_ids).issubset(allowed):
        raise ValueError("User cannot export those branches.")


def _request_rows(company: Company, branch_ids: list[str], start_date, end_date) -> list[dict[str, Any]]:
    tasks = TaskInstance.objects.filter(company=company, branch_id__in=branch_ids)
    if start_date:
        tasks = tasks.filter(created_at__date__gte=start_date)
    if end_date:
        tasks = tasks.filter(created_at__date__lte=end_date)
    return [
        {
            "kind": "task",
            "id": str(task.id),
            "branch": task.branch.name,
            "template": task.template.name,
            "status": task.status,
            "due_at": task.due_at.isoformat(),
            "assigned_user": task.assigned_user_id,
        }
        for task in tasks.select_related("branch", "template", "assigned_user")
    ]


def _evidence_rows(company: Company, branch_ids: list[str], start_date, end_date) -> list[dict[str, Any]]:
    evidence = EvidenceItem.objects.filter(company=company, branch_id__in=branch_ids)
    if start_date:
        evidence = evidence.filter(created_at__date__gte=start_date)
    if end_date:
        evidence = evidence.filter(created_at__date__lte=end_date)
    return [
        {
            "kind": "evidence",
            "id": str(item.id),
            "branch": item.branch.name,
            "task_instance": str(item.task_instance_id),
            "status": item.status,
            "duplicate_risk_score": item.duplicate_risk_score,
            "face_detected": item.face_detected,
        }
        for item in evidence.select_related("branch", "task_instance")
    ]


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=sorted({key for row in rows for key in row.keys()}))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _pdf_bytes(title: str, lines: list[str]) -> bytes:
    """Render a one-page PDF, shaping Arabic text so glyphs connect correctly."""
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font_path = Path(__file__).resolve().parent / "assets" / "fonts" / "Amiri-Regular.ttf"
    pdfmetrics.registerFont(TTFont("Amiri", str(font_path)))

    buffer = io.BytesIO()
    doc = canvas.Canvas(buffer, pagesize=A4)
    doc.setFont("Amiri", 14)
    doc.drawString(50, 790, get_display(reshape(title)))
    doc.setFont("Amiri", 11)
    y = 770
    for line in lines:
        doc.drawString(50, y, get_display(reshape(line)))
        y -= 16
    doc.save()
    return buffer.getvalue()


def _artifact_bytes(
    company: Company,
    branch_ids: list[str],
    categories: list[str],
    export_type: str,
    start_date,
    end_date,
) -> tuple[bytes, str]:
    rows: list[dict[str, Any]] = []
    if "tasks" in categories:
        rows.extend(_request_rows(company, branch_ids, start_date, end_date))
    if "evidence" in categories:
        rows.extend(_evidence_rows(company, branch_ids, start_date, end_date))
    if export_type == ExportType.CSV:
        return _csv_bytes(rows), "export.csv"
    if export_type == ExportType.PDF:
        lines = [f"Rows: {len(rows)}", f"Branches: {len(branch_ids)}"] + [f"{row['kind']} {row['id']} {row.get('status', '')}" for row in rows[:20]]
        return _pdf_bytes(f"Export {company.code}", lines), "summary.pdf"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("data.csv", _csv_bytes(rows))
        archive.writestr("summary.pdf", _pdf_bytes(f"Export {company.code}", [f"Rows: {len(rows)}", f"Branches: {len(branch_ids)}"]))
    return buffer.getvalue(), "archive.zip"


@transaction.atomic
def prepare_export_request(
    *,
    company: Company,
    user: User,
    export_type: str,
    branch_ids: list[str],
    categories: list[str],
    start_date=None,
    end_date=None,
) -> ExportRequest:
    if not branch_ids:
        branch_ids = accessible_branch_ids(company, user)
    _ensure_authorized(company, user, branch_ids)
    return ExportRequest.objects.create(
        company=company,
        requested_by=user,
        export_type=export_type,
        branch_ids=branch_ids,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        download_token=secrets.token_urlsafe(32),
        expires_at=timezone.now() + timedelta(hours=24),
    )


@transaction.atomic
def complete_export_request(export_request_id: str) -> ExportRequest:
    export_request = ExportRequest.objects.get(id=export_request_id)
    data, file_name = _artifact_bytes(
        export_request.company,
        export_request.branch_ids,
        export_request.categories,
        export_request.export_type,
        export_request.start_date,
        export_request.end_date,
    )
    path = export_storage_root() / f"{export_request.download_token}-{file_name}"
    path.write_bytes(data)
    export_request.file_name = path.name
    export_request.status = ExportStatus.COMPLETED
    export_request.completed_at = timezone.now()
    export_request.save(update_fields=["file_name", "status", "completed_at", "updated_at"])
    _audit, outbox_event = emit_audit_and_outbox(
        audit_event_type="EXPORT_REQUESTED",
        audit_target_type="export_request",
        audit_target_id=str(export_request.id),
        actor_id=str(export_request.requested_by_id),
        branch_id="",
        audit_metadata={
            "export_type": export_request.export_type,
            "branch_ids": export_request.branch_ids,
        },
        outbox=quick_event(
            event_name="exports.completed",
            aggregate_type="export_request",
            aggregate_id=str(export_request.id),
            company_id=str(export_request.company_id),
            request_id=str(export_request.id),
            requested_by=str(export_request.requested_by_id),
            file_name=export_request.file_name,
        ),
    )
    emit_for_outbox_event(outbox_event)
    return export_request


@transaction.atomic
def create_export_request(
    *,
    company: Company,
    user: User,
    export_type: str,
    branch_ids: list[str],
    categories: list[str],
    start_date=None,
    end_date=None,
) -> ExportRequest:
    export_request = prepare_export_request(
        company=company,
        user=user,
        export_type=export_type,
        branch_ids=branch_ids,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
    )
    return complete_export_request(str(export_request.id))


def list_export_requests(company: Company, user: User):
    branch_ids = accessible_branch_ids(company, user)
    requests = ExportRequest.objects.filter(company=company).order_by("-created_at")
    return [request for request in requests if set(request.branch_ids).intersection(branch_ids)]


def export_download_response(company: Company, user: User, token: str) -> FileResponse:
    export_request = ExportRequest.objects.get(company=company, download_token=token)
    if export_request.expires_at <= timezone.now():
        export_request.status = ExportStatus.EXPIRED
        export_request.save(update_fields=["status", "updated_at"])
        raise ValueError("Export has expired.")
    _ensure_authorized(company, user, export_request.branch_ids)
    path = export_storage_root() / export_request.file_name
    export_request.downloaded_at = timezone.now()
    export_request.save(update_fields=["downloaded_at", "updated_at"])
    record_audit_event(
        event_type="EXPORT_DOWNLOADED",
        target_type="export_request",
        target_id=str(export_request.id),
        actor_id=str(user.id),
        branch_id="",
        metadata={"token_fingerprint": hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]},
    )
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)
