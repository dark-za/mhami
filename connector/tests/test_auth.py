"""H-04: connector authentication tests."""

from __future__ import annotations

import time

import pytest

from src.auth import (
    ReplayGuard,
    compute_signature,
    load_secret,
    verify_request,
)


def test_signature_roundtrip():
    secret = "test-secret"
    ts = "1700000000"
    nonce = "abc"
    body = b"{\"x\":1}"
    sig = compute_signature(secret, timestamp=ts, nonce=nonce, body=body)
    verify_request(
        secret,
        headers={
            "x-mhami-signature": sig,
            "x-mhami-timestamp": ts,
            "x-mhami-nonce": nonce,
        },
        body=body,
    )


def test_missing_signature_is_rejected():
    with pytest.raises(ValueError):
        verify_request(
            "secret",
            headers={"x-mhami-signature": "", "x-mhami-timestamp": "1", "x-mhami-nonce": "n"},
            body=b"",
        )


def test_tampered_body_is_rejected():
    secret = "test-secret"
    ts = str(int(time.time()))
    nonce = "nonce-1"
    body = b"original"
    sig = compute_signature(secret, timestamp=ts, nonce=nonce, body=body)
    with pytest.raises(ValueError):
        verify_request(
            secret,
            headers={
                "x-mhami-signature": sig,
                "x-mhami-timestamp": ts,
                "x-mhami-nonce": nonce,
            },
            body=b"tampered",
        )


def test_stale_timestamp_is_rejected():
    secret = "test-secret"
    ts = "1000"  # very old
    nonce = "nonce-stale"
    body = b""
    sig = compute_signature(secret, timestamp=ts, nonce=nonce, body=body)
    with pytest.raises(ValueError):
        verify_request(
            secret,
            headers={
                "x-mhami-signature": sig,
                "x-mhami-timestamp": ts,
                "x-mhami-nonce": nonce,
            },
            body=body,
        )


def test_replay_is_rejected():
    secret = "test-secret"
    ts = str(int(time.time()))
    nonce = "nonce-replay"
    body = b"x"
    sig = compute_signature(secret, timestamp=ts, nonce=nonce, body=body)
    headers = {
        "x-mhami-signature": sig,
        "x-mhami-timestamp": ts,
        "x-mhami-nonce": nonce,
    }
    guard = ReplayGuard(freshness_seconds=60)
    verify_request(secret, headers=headers, body=body, replay_guard=guard)
    with pytest.raises(ValueError):
        verify_request(secret, headers=headers, body=body, replay_guard=guard)


def test_load_secret_raises_when_missing(monkeypatch):
    monkeypatch.delenv("CONNECTOR_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        load_secret()
