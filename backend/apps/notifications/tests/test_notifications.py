from __future__ import annotations

import pytest
from django.test import Client

from apps.audit.models import AuditEvent
from apps.notifications.models import Notification
from apps.notifications.services import create_notification, emit_for_outbox_event, mark_notification_read, mark_notifications_read
from apps.organizations.models import CompanyRole
from apps.platform_core.services import record_outbox_event


pytestmark = pytest.mark.django_db


def _company_owner(make_user, make_company, make_membership, login_id="notify-owner", code="notify-co"):
    owner = make_user(login_id=login_id, display_name="Owner")
    company = make_company(name="Notify Co", code=code, industry="other", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    return owner, company


def test_notification_company_scoping(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    other_owner, other_company = _company_owner(
        make_user, make_company, make_membership, "notify-other-owner", "notify-co-2",
    )
    create_notification(
        company=company, user=owner, notification_type="backup.completed", title="Backup done", body="Artifact ready."
    )
    assert Notification.objects.filter(company=company, user=owner).count() == 1
    assert Notification.objects.filter(company=other_company, user=other_owner).count() == 0
    assert Notification.objects.filter(company=company, user=other_owner).count() == 0


def test_unread_list_via_api(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    first = create_notification(
        company=company, user=owner, notification_type="backup.completed", title="Backup done", body="Artifact ready."
    )
    create_notification(
        company=company, user=owner, notification_type="exports.completed", title="Export ready", severity="success"
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.get("/api/v1/notifications/")
    assert response.status_code == 200
    payload = response.json()["notifications"]
    assert len(payload) == 2
    assert all(item["read_at"] is None for item in payload)
    assert payload[0]["id"] == str(first.id) or payload[1]["id"] == str(first.id)


def test_mark_read_single_and_audit(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    notification = create_notification(
        company=company, user=owner, notification_type="backup.completed", title="Backup done"
    )
    assert notification is not None
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.post(f"/api/v1/notifications/{notification.id}/read")
    assert response.status_code == 200
    assert response.json()["read_at"] is not None
    assert AuditEvent.objects.filter(event_type="NOTIFICATION_READ", target_id=str(notification.id)).count() == 1
    assert AuditEvent.objects.filter(event_type="NOTIFICATION_CREATED", target_id=str(notification.id)).count() == 1


def test_mark_read_batch_and_audit(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    ids = [
        notification.id
        for notification in [
            create_notification(company=company, user=owner, notification_type="backup.completed", title="One"),
            create_notification(company=company, user=owner, notification_type="backup.completed", title="Two"),
        ]
        if notification is not None
    ]
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.post(
        "/api/v1/notifications/read",
        data={"ids": [str(notification_id) for notification_id in ids]},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["marked"] == 2
    assert Notification.objects.filter(company=company, user=owner, read_at__isnull=True).count() == 0
    assert AuditEvent.objects.filter(event_type="NOTIFICATION_READ", metadata={"batch": True}).count() == 2


def test_outbox_event_emits_owner_notification(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    event = record_outbox_event(
        event_name="backup.completed",
        aggregate_type="backup_run",
        aggregate_id="00000000-0000-0000-0000-000000000001",
        payload={"company_id": str(company.id), "artifact_name": "abc.zip"},
    )
    emit_for_outbox_event(event)
    notification = Notification.objects.get(company=company, user=owner)
    assert notification.type == "backup.completed"
    assert notification.severity == "success"
    event.refresh_from_db()
    assert event.published_at is not None


def test_outbox_consumption_is_idempotent(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    event = record_outbox_event(
        event_name="backup.restore.completed",
        aggregate_type="backup_run",
        aggregate_id="00000000-0000-0000-0000-000000000002",
        payload={"company_id": str(company.id), "restore_id": "00000000-0000-0000-0000-000000000003"},
    )
    emit_for_outbox_event(event)
    emit_for_outbox_event(event)
    assert Notification.objects.filter(company=company, user=owner).count() == 1


def test_mark_notifications_read_ignores_other_users(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    other = make_user(login_id="notify-member", display_name="Member")
    make_membership(user=other, company=company, role=CompanyRole.MONITOR)
    notification = create_notification(company=company, user=other, notification_type="exports.completed", title="Export")
    assert notification is not None
    count = mark_notifications_read([str(notification.id)], company=company, user=owner)
    assert count == 0
    notification.refresh_from_db()
    assert notification.read_at is None


def test_mark_notification_read_is_idempotent(make_user, make_company, make_membership):
    owner, company = _company_owner(make_user, make_company, make_membership)
    notification = create_notification(company=company, user=owner, notification_type="backup.completed", title="One")
    assert notification is not None
    mark_notification_read(notification, actor=owner)
    mark_notification_read(notification, actor=owner)
    assert AuditEvent.objects.filter(event_type="NOTIFICATION_READ", target_id=str(notification.id)).count() == 1
