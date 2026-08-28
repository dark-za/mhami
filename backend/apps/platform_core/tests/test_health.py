from __future__ import annotations

import pytest
from django.test import Client

from apps.platform_core import metrics


def test_live_health_endpoint():
    response = Client().get("/api/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_metrics_endpoint_reports_operational_signals(settings, monkeypatch):
    settings.METRICS_TOKEN = "test-metrics-token"
    monkeypatch.setattr(metrics, "_redis_metrics", lambda: (1, {"default": 2, "media": 3, "ai": 4}))
    monkeypatch.setattr(metrics, "_worker_count", lambda: 1)

    client = Client()
    assert client.get("/api/v1/metrics").status_code == 403
    response = client.get("/api/v1/metrics", HTTP_X_METRICS_TOKEN="test-metrics-token")

    assert response.status_code == 200
    assert b"platform_database_up 1" in response.content
    assert b'platform_celery_queue_depth{queue="media"} 3' in response.content
    assert b"platform_media_disk_free_bytes" in response.content
