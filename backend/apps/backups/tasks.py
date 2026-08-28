from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings

from apps.identity.models import User
from apps.platform_core.services import broker_available
from apps.tenancy.models import Company

from .external_storage import (
    ExternalStorageConfigurationError,
    ExternalStorageError,
    ExternalStorageIntegrityError,
    ExternalStorageUnavailable,
    upload_artifact,
)
from .models import BackupRun, BackupStatus
from .services import backup_storage_root, complete_backup_run, create_backup_run, prepare_backup_run

logger = logging.getLogger(__name__)


@shared_task(name="apps.backups.run_backup_run")
def run_backup_run(
    backup_run_id: str,
    include_private_media: bool = True,
    include_configuration: bool = True,
    include_tenant_state: bool = True,
) -> str:
    backup_run = BackupRun.objects.get(id=backup_run_id)
    try:
        complete_backup_run(
            backup_run_id,
            include_private_media=include_private_media,
            include_configuration=include_configuration,
            include_tenant_state=include_tenant_state,
        )
    except Exception as exc:
        backup_run.status = BackupStatus.FAILED
        backup_run.error_message = str(exc)
        backup_run.save(update_fields=["status", "error_message"])
        raise
    # INFRA-03: mirror the local artefact to the external storage
    # destination. Failures are recorded on the run so an operator can
    # triage, but they do not invalidate the on-disk copy.
    if getattr(settings, "BACKUP_EXTERNAL_URI", ""):
        run_external_upload.delay(str(backup_run.id))
    return str(backup_run.id)


@shared_task(name="apps.backups.run_external_upload")
def run_external_upload(backup_run_id: str) -> str:
    """INFRA-03: upload a completed backup to ``BACKUP_EXTERNAL_URI``.

    The task reads the encrypted Fernet artefact, re-wraps it under
    the configured ``BACKUP_EXTERNAL_KEY_ID`` KEK and writes the
    envelope to S3 with least-privilege credentials. Audit and outbox
    events are emitted by :mod:`apps.backups.services` for the local
    completion; this task records the external mirror as a separate
    event so a quota or outage on the remote side never invalidates
    the on-disk backup.
    """
    backup_run = BackupRun.objects.get(id=backup_run_id)
    artifact_path = backup_storage_root() / backup_run.artifact_name
    if not artifact_path.is_file():
        backup_run.error_message = "Local artefact missing before external upload."
        backup_run.save(update_fields=["error_message"])
        raise ExternalStorageError(backup_run.error_message)
    payload = artifact_path.read_bytes()
    company = backup_run.company
    try:
        result = upload_artifact(
            plaintext=payload,
            company_code=company.code,
            artifact_name=artifact_path.name,
            extra_metadata={
                "backup_run_id": str(backup_run.id),
                "manifest_sha256": backup_run.manifest_sha256 or "",
            },
        )
    except ExternalStorageConfigurationError as exc:
        backup_run.error_message = f"External storage misconfigured: {exc}"
        backup_run.save(update_fields=["error_message"])
        raise
    except ExternalStorageUnavailable as exc:
        backup_run.error_message = f"External storage unavailable: {exc}"
        backup_run.save(update_fields=["error_message"])
        raise
    except ExternalStorageIntegrityError as exc:
        backup_run.error_message = f"External storage integrity failure: {exc}"
        backup_run.save(update_fields=["error_message"])
        raise
    else:
        manifest = dict(backup_run.manifest or {})
        manifest["external_upload"] = {
            "key_id": result.key_id,
            "remote_uri": result.remote_uri,
            "encrypted_sha256": result.encrypted_sha256,
            "object_version": result.object_version,
            "retention_days": result.retention_days,
        }
        backup_run.manifest = manifest
        backup_run.save(update_fields=["manifest"])
        logger.info(
            "backup.external_upload.completed",
            extra={
                "backup_run_id": str(backup_run.id),
                "remote_uri": result.remote_uri,
                "key_id": result.key_id,
            },
        )
    return str(backup_run.id)


@shared_task(name="apps.backups.create_daily_backups")
def create_daily_backups() -> int:
    created = 0
    for company in Company.objects.exclude(owner__isnull=True).select_related("owner"):
        create_backup_run(company, company.owner)
        created += 1
    return created


def enqueue_backup_run(
    company: Company,
    user: User,
    include_private_media: bool = True,
    include_configuration: bool = True,
    include_tenant_state: bool = True,
) -> BackupRun:
    if broker_available():
        backup_run = prepare_backup_run(
            company,
            user,
            include_private_media=include_private_media,
            include_configuration=include_configuration,
            include_tenant_state=include_tenant_state,
        )
        run_backup_run.delay(
            str(backup_run.id),
            include_private_media,
            include_configuration,
            include_tenant_state,
        )
        return backup_run
    return create_backup_run(
        company,
        user,
        include_private_media=include_private_media,
        include_configuration=include_configuration,
        include_tenant_state=include_tenant_state,
    )
