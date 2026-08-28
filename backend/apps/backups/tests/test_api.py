from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, time
from pathlib import Path

import pytest
from django.utils import timezone

from apps.backups.models import RestoreRun
from apps.backups.services import download_backup_artifact, restore_backup_run
from apps.evidence.models import EvidenceItem
from apps.organizations.models import CompanyRole
from apps.tasks.services import schedule_due_tasks


pytestmark = pytest.mark.django_db(transaction=True, databases="__all__")


def _context(
    make_user,
    make_company,
    make_membership,
    make_branch,
    make_template,
    make_template_version,
    make_schedule,
):
    """Set up owner+company+branch with one scheduled task ready to back up."""
    owner = make_user(login_id="backup-owner", display_name="Owner")
    company = make_company(name="Backup Co", code="backup-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    branch = make_branch(company=company, code="main", name="Main")
    template = make_template(company=company, branch=branch, assigned_user=owner)
    make_template_version(template=template)
    make_schedule(company=company, branch=branch, template=template, scheduled_time=time(9, 0))
    schedule_due_tasks(moment=timezone.make_aware(datetime(2026, 1, 5, 9, 30)))
    return owner, company, branch


def test_backup_create_download_restore(
    tmp_path,
    settings,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_evidence_item, force_login_company,
):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.BACKUP_STORAGE_ROOT = tmp_path / "backups"
    settings.BACKUP_RESTORE_ROOT = tmp_path / "restores"
    owner, company, branch = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    evidence = make_evidence_item(
        company=company, branch=branch, submitted_by=owner,
    )
    source_media = Path(settings.MEDIA_ROOT) / "evidence" / "private"
    source_media.mkdir(parents=True)
    (source_media / evidence.private_media_name).write_bytes(b"private-image-bytes")
    (source_media / evidence.blurred_media_name).write_bytes(b"blurred-derivative-bytes")
    client = force_login_company(owner, company)

    run = client.post(
        "/api/v1/backups/runs",
        data={"include_private_media": True, "include_configuration": True, "include_tenant_state": True},
        content_type="application/json",
    )
    assert run.status_code == 201
    run_id = run.json()["id"]
    assert run.json()["artifact_sha256"]
    assert run.json()["manifest_sha256"]

    download = client.get(f"/api/v1/backups/download/{run_id}")
    assert download.status_code == 200
    with zipfile.ZipFile(io.BytesIO(b"".join(download.streaming_content))) as artifact:
        manifest = json.loads(artifact.read("manifest.json"))
        assert manifest["counts"]["database"]["evidence.evidenceitem"] == 1
        assert artifact.read(f"media/evidence/private/{evidence.private_media_name}") == b"private-image-bytes"
        assert artifact.read(f"media/evidence/private/{evidence.blurred_media_name}") == b"blurred-derivative-bytes"

    restore = client.post(
        "/api/v1/backups/restore",
        data={"backup_run_id": run_id, "target_name": "phase12", "confirmation": f"RESTORE {run_id}"},
        content_type="application/json",
    )
    assert restore.status_code == 201, RestoreRun.objects.latest("created_at").report
    assert restore.json()["verified_database"] is True
    assert restore.json()["verified_media"] is True
    assert restore.json()["report"]["restored_counts"]["evidence.evidenceitem"] == 1
    assert (
        Path(settings.BACKUP_RESTORE_ROOT) / "phase12" / "media" / "evidence" / "private" / evidence.private_media_name
    ).read_bytes() == b"private-image-bytes"
    assert (
        Path(settings.BACKUP_RESTORE_ROOT) / "phase12" / "media" / "evidence" / "private" / evidence.blurred_media_name
    ).read_bytes() == b"blurred-derivative-bytes"
    assert EvidenceItem.objects.filter(company=company).count() == 1


def test_restore_rejects_default_target_and_tampered_archive(
    tmp_path,
    settings,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    force_login_company,
):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.BACKUP_STORAGE_ROOT = tmp_path / "backups"
    settings.BACKUP_RESTORE_ROOT = tmp_path / "restores"
    owner, company, _branch = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    client = force_login_company(owner, company)
    run = client.post("/api/v1/backups/runs", data={}, content_type="application/json")
    run_id = run.json()["id"]

    default_target = client.post(
        "/api/v1/backups/restore",
        data={"backup_run_id": run_id, "target_name": "default", "confirmation": f"RESTORE {run_id}"},
        content_type="application/json",
    )
    assert default_target.status_code == 400
    assert not (Path(settings.BACKUP_RESTORE_ROOT) / "default").exists()

    artifact = download_backup_artifact(company, run_id)
    artifact.write_bytes(artifact.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="integrity"):
        restore_backup_run(company, owner, run_id, "tampered", f"RESTORE {run_id}")
    assert not (Path(settings.BACKUP_RESTORE_ROOT) / "tampered").exists()
