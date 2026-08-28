from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.exports.models import ExportStatus
from apps.exports.tasks import enqueue_export_request


pytestmark = pytest.mark.django_db


def test_enqueue_export_falls_back_to_sync_without_broker(tmp_path, settings, make_user, make_company, make_membership, make_branch):
    settings.MEDIA_ROOT = tmp_path / "media"
    owner = make_user(login_id="enqueue-owner", display_name="Owner")
    company = make_company(name="Enqueue Co", code="enqueue-co", owner=owner)
    make_membership(user=owner, company=company)
    branch = make_branch(company=company, code="main", name="Main")
    with patch("apps.exports.tasks.broker_available", return_value=False):
        export_request = enqueue_export_request(
            company=company,
            user=owner,
            export_type="csv",
            branch_ids=[str(branch.id)],
            categories=["tasks"],
        )
    export_request.refresh_from_db()
    assert export_request.status == ExportStatus.COMPLETED
    assert export_request.file_name.endswith(".csv")


def test_enqueue_export_queues_when_broker_available(make_user, make_company, make_membership, make_branch):
    owner = make_user(login_id="enqueue-owner", display_name="Owner")
    company = make_company(name="Enqueue Co", code="enqueue-co", owner=owner)
    make_membership(user=owner, company=company)
    branch = make_branch(company=company, code="main", name="Main")
    with (
        patch("apps.exports.tasks.broker_available", return_value=True),
        patch("apps.exports.tasks.run_export_request.delay") as delay,
    ):
        export_request = enqueue_export_request(
            company=company,
            user=owner,
            export_type="csv",
            branch_ids=[str(branch.id)],
            categories=["tasks"],
        )
    delay.assert_called_once_with(str(export_request.id))
    export_request.refresh_from_db()
    assert export_request.status == ExportStatus.QUEUED