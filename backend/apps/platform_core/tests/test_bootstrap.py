from __future__ import annotations

from django.test import Client


def test_bootstrap_endpoint_returns_foundation_payload():
    response = Client().get("/api/v1/bootstrap")
    assert response.status_code == 200
    payload = response.json()
    assert payload["current_user"]["is_authenticated"] is False
    assert "platform_core" in payload["enabled_modules"]
