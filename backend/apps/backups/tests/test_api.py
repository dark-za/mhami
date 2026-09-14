from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, time
from pathlib import Path

import pytest
from django.utils import timezone

from apps.backups.models import RestoreRun
from apps.backups.models import BackupPolicy
from apps.audit.models import AuditEvent
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


def test_owner_can_update_backup_policy_and_change_is_audited(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule, force_login_company,
):
    owner, company, _branch = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    client = force_login_company(owner, company)

    response = client.put(
        "/api/v1/backups/policy",
        data={
            "destination_name": "local-secondary",
            "schedule_cron": "15 3 * * *",
            "rpo_hours": 12,
            "rto_hours": 8,
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    policy = BackupPolicy.objects.get(company=company)
    assert policy.destination_name == "local-secondary"
    assert policy.schedule_cron == "15 3 * * *"
    assert policy.rpo_hours == 12
    assert policy.rto_hours == 8
    assert policy.encrypted is True
    assert policy.updated_by_id == owner.id
    assert AuditEvent.objects.filter(event_type="BACKUP_POLICY_UPDATED", target_id=str(policy.id)).exists()


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


def test_download_returns_zip_without_plaintext_sibling(
    tmp_path,
    settings,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    force_login_company,
):
    """Owner download yields a readable ZIP but creates no plaintext file on disk."""
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

    artifact_path = download_backup_artifact(company, run_id)
    assert artifact_path.suffix == ".enc"
    storage_root = Path(settings.BACKUP_STORAGE_ROOT)
    siblings = list(storage_root.glob(f"{run_id}-backup.zip*"))
    assert siblings == [artifact_path]

    download = client.get(f"/api/v1/backups/download/{run_id}")
    assert download.status_code == 200
    content = b"".join(download.streaming_content)
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        assert zf.testzip() is None
        assert "manifest.json" in zf.namelist()

    siblings_after = list(storage_root.glob(f"{run_id}-backup.zip*"))
    assert siblings_after == [artifact_path]


def test_download_tampered_artifact_rejected(
    tmp_path,
    settings,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    force_login_company,
):
    """Repeated download of a tampered artifact fails integrity check."""
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

    good = client.get(f"/api/v1/backups/download/{run_id}")
    assert good.status_code == 200

    artifact_path = download_backup_artifact(company, run_id)
    artifact_path.write_bytes(artifact_path.read_bytes() + b"X")

    tampered = client.get(f"/api/v1/backups/download/{run_id}")
    assert tampered.status_code == 400


def test_restore_from_encrypted_path_succeeds(
    tmp_path,
    settings,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    force_login_company,
):
    """Restore works when fed the canonical encrypted storage path."""
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

    encrypted_path = download_backup_artifact(company, run_id)
    assert encrypted_path.suffix == ".enc"

    restore = client.post(
        "/api/v1/backups/restore",
        data={"backup_run_id": run_id, "target_name": "encpath", "confirmation": f"RESTORE {run_id}"},
        content_type="application/json",
    )
    assert restore.status_code == 201
    assert restore.json()["verified_database"] is True


def test_download_rejected_for_unauthorized_role(
    tmp_path,
    settings,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    force_login_company,
):
    """Non-OWNER role cannot download backup artifacts."""
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.BACKUP_STORAGE_ROOT = tmp_path / "backups"
    settings.BACKUP_RESTORE_ROOT = tmp_path / "restores"
    owner, company, _branch = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    client_owner = force_login_company(owner, company)
    run = client_owner.post("/api/v1/backups/runs", data={}, content_type="application/json")
    run_id = run.json()["id"]

    viewer = make_user(login_id="backup-viewer", display_name="Viewer")
    make_membership(user=viewer, company=company, role=CompanyRole.MONITOR)
    client_viewer = force_login_company(viewer, company)
    resp = client_viewer.get(f"/api/v1/backups/download/{run_id}")
    assert resp.status_code == 403
