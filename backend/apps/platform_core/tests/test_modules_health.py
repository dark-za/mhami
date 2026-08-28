from __future__ import annotations

from django.test import Client


def test_modules_health_endpoint_lists_core_modules():
    response = Client().get("/api/v1/health/modules")
    assert response.status_code == 200
    payload = response.json()
    assert any(module["slug"] == "platform_core" for module in payload["modules"])
