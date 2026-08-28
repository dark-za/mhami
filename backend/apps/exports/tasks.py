from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from apps.identity.models import User
from apps.platform_core.services import broker_available
from apps.tenancy.models import Company

from .models import ExportRequest, ExportStatus
from .services import complete_export_request, create_export_request, prepare_export_request


@shared_task(name="apps.exports.cleanup_expired_exports")
def cleanup_expired_exports() -> int:
    expired = ExportRequest.objects.filter(status__in=[ExportStatus.COMPLETED, ExportStatus.QUEUED], expires_at__lt=timezone.now())
    count = expired.update(status=ExportStatus.EXPIRED)
    return count


@shared_task(name="apps.exports.run_export_request")
def run_export_request(export_request_id: str) -> str:
    export_request = ExportRequest.objects.get(id=export_request_id)
    try:
        complete_export_request(export_request_id)
    except Exception as exc:
        export_request.status = ExportStatus.FAILED
        export_request.last_error = str(exc)
        export_request.save(update_fields=["status", "last_error", "updated_at"])
        raise
    return str(export_request_id)


def enqueue_export_request(
    *,
    company: Company,
    user: User,
    export_type: str,
    branch_ids: list[str],
    categories: list[str],
    start_date=None,
    end_date=None,
) -> ExportRequest:
    if broker_available():
        export_request = prepare_export_request(
            company=company,
            user=user,
            export_type=export_type,
            branch_ids=branch_ids,
            categories=categories,
            start_date=start_date,
            end_date=end_date,
        )
        run_export_request.delay(str(export_request.id))
        return export_request
    return create_export_request(
        company=company,
        user=user,
        export_type=export_type,
        branch_ids=branch_ids,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
    )