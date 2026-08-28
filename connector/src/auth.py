"""Authentication for the Mhami connector.

H-04: the connector authenticates every inbound request with an HMAC
signature over ``timestamp + nonce + body``. The platform issues the
shared secret out-of-band and rotates it on a defined schedule. A
request is accepted only if:

* the signature matches the canonical string;
* the timestamp is within the configured freshness window;
* the nonce has not been seen before (replay store).

The replay store is intentionally simple (in-memory with a TTL) so the
connector can be deployed as a single container. The container reads
its own ``CONNECTOR_API_KEY`` from the secret manager, never from a
request body, and refuses to start if the key is missing.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Mapping

import os

DEFAULT_FRESHNESS_SECONDS = 300


@dataclass
class ReplayGuard:
    """TTL-based replay store.

    The store keeps the most recent ``max_entries`` nonces. Entries
    older than ``freshness_seconds`` are pruned on insertion. The
    implementation is in-process, which is fine for a single-tenant
    container; multi-replica deployments must share a Redis or
    database-backed store.
    """

    freshness_seconds: int = DEFAULT_FRESHNESS_SECONDS
    max_entries: int = 10_000
    _store: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self._store is None:
            self._store = {}

    def seen(self, nonce: str, now: float | None = None) -> bool:
        if not nonce or self._store is None:
            return False
        ts = now if now is not None else time.time()
        self._prune(ts)
        if nonce in self._store:
            return True
        self._store[nonce] = ts
        return False

    def _prune(self, now: float) -> None:
        if self._store is None:
            return
        expired = [n for n, ts in self._store.items() if now - ts > self.freshness_seconds]
        for nonce in expired:
            self._store.pop(nonce, None)
        if len(self._store) > self.max_entries:
            # Drop the oldest entries to bound memory.
            ordered = sorted(self._store.items(), key=lambda kv: kv[1])
            for nonce, _ in ordered[: len(self._store) - self.max_entries]:
                self._store.pop(nonce, None)


def _canonical_string(*, timestamp: str, nonce: str, body: bytes) -> bytes:
    digest = hashlib.sha256(body or b"").hexdigest()
    return f"{timestamp}\n{nonce}\n{digest}".encode("utf-8")


def compute_signature(secret: str, *, timestamp: str, nonce: str, body: bytes) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        _canonical_string(timestamp=timestamp, nonce=nonce, body=body),
        hashlib.sha256,
    ).hexdigest()


def verify_request(
    secret: str,
    *,
    headers: Mapping[str, str],
    body: bytes,
    replay_guard: ReplayGuard | None = None,
    freshness_seconds: int = DEFAULT_FRESHNESS_SECONDS,
) -> None:
    """Raise ``ValueError`` if the request signature is missing, stale, or replayed."""
    if not secret:
        raise ValueError("CONNECTOR_API_KEY is not configured.")
    signature = headers.get("x-mhami-signature", "")
    timestamp = headers.get("x-mhami-timestamp", "")
    nonce = headers.get("x-mhami-nonce", "")
    if not signature or not timestamp or not nonce:
        raise ValueError("Missing signature headers.")
    try:
        ts = float(timestamp)
    except ValueError as exc:
        raise ValueError("Invalid timestamp.") from exc
    if abs(time.time() - ts) > freshness_seconds:
        raise ValueError("Signature timestamp is outside the freshness window.")
    expected = compute_signature(secret, timestamp=timestamp, nonce=nonce, body=body)
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Signature mismatch.")
    if replay_guard is not None and replay_guard.seen(nonce):
        raise ValueError("Nonce has been replayed.")


def load_secret() -> str:
    secret = os.environ.get("CONNECTOR_API_KEY", "")
    if not secret:
        raise RuntimeError("CONNECTOR_API_KEY is required.")
    return secret
