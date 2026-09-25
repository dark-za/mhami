"""Tests for X-Request-ID sanitisation."""

from __future__ import annotations

import uuid

from django.test import Client

from apps.platform_core.request_id import sanitize_request_id


def test_sanitize_generates_uuid_when_missing():
    value = sanitize_request_id(None)
    assert str(uuid.UUID(value)) == value


def test_sanitize_generates_uuid_for_empty_string():
    value = sanitize_request_id("")
    assert str(uuid.UUID(value)) == value


def test_sanitize_passthrough_for_valid_uuid():
    raw = "123e4567-e89b-12d3-a456-426614174000"
    assert sanitize_request_id(raw) == raw


def test_sanitize_strips_whitespace_around_uuid():
    raw = "  123e4567-e89b-12d3-a456-426614174000  "
    assert sanitize_request_id(raw) == "123e4567-e89b-12d3-a456-426614174000"


def test_sanitize_rejects_non_uuid():
    value = sanitize_request_id("attacker;<script>alert(1)</script>")
    assert str(uuid.UUID(value)) == value
    assert value != "attacker;<script>alert(1)</script>"


def test_middleware_replaces_malicious_header():
    response = Client().get(
        "/api/health/live",
        HTTP_X_REQUEST_ID="not-a-uuid' OR 1=1 --",
    )
    assert response.status_code == 200
    header = response["X-Request-ID"]
    assert str(uuid.UUID(header)) == header


def test_middleware_passes_valid_uuid_header():
    raw = "123e4567-e89b-12d3-a456-426614174000"
    response = Client().get("/api/health/live", HTTP_X_REQUEST_ID=raw)
    assert response.status_code == 200
    assert response["X-Request-ID"] == raw
