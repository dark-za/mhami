from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.backups.models import BackupStatus
from apps.backups.tasks import enqueue_backup_run


pytestmark = pytest.mark.django_db


def test_enqueue_backup_falls_back_to_sync_without_broker(tmp_path, settings, make_user, make_company, make_membership, make_branch):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.BACKUP_STORAGE_ROOT = tmp_path / "backups"
    owner = make_user(login_id="enqueue-backup-owner", display_name="Owner")
    company = make_company(name="Enqueue Backup Co", code="enqueue-backup-co", owner=owner)
    make_membership(user=owner, company=company)
    make_branch(company=company, code="main", name="Main")
    with patch("apps.backups.tasks.broker_available", return_value=False):
        backup_run = enqueue_backup_run(company, owner)
    backup_run.refresh_from_db()
    assert backup_run.status == BackupStatus.COMPLETED
    # H-05: the on-disk artefact is the Fernet-wrapped payload, so the
    # extension is ``.zip.enc`` rather than ``.zip``.
    assert backup_run.artifact_name.endswith(".zip.enc")


def test_enqueue_backup_queues_when_broker_available(make_user, make_company, make_membership, make_branch):
    owner = make_user(login_id="enqueue-backup-owner", display_name="Owner")
    company = make_company(name="Enqueue Backup Co", code="enqueue-backup-co", owner=owner)
    make_membership(user=owner, company=company)
    make_branch(company=company, code="main", name="Main")
    with (
        patch("apps.backups.tasks.broker_available", return_value=True),
        patch("apps.backups.tasks.run_backup_run.delay") as delay,
    ):
        backup_run = enqueue_backup_run(company, owner)
    delay.assert_called_once_with(str(backup_run.id), True, True, True)
    backup_run.refresh_from_db()
    assert backup_run.status == BackupStatus.REQUESTED