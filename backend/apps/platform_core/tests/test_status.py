from __future__ import annotations

import pytest
from django.test import Client


pytestmark = pytest.mark.django_db


def test_system_status_endpoint_reports_metrics(make_user):
    user = make_user(login_id="system-admin", is_staff=True)
    client = Client()
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "metrics" in payload
    assert "backups" in payload["metrics"]


def test_system_status_rejects_public_access():
    response = Client().get("/api/v1/status")
    assert response.status_code == 403
