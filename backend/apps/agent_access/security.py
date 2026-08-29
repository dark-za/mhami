from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed

from .models import AgentGrant


@dataclass(frozen=True, slots=True)
class VerifiedAgentRequest:
    grant: AgentGrant
    request_id: UUID


def _signature_value(raw_signature: str) -> str:
    if raw_signature.startswith("sha256="):
        return raw_signature.removeprefix("sha256=")
    return raw_signature


def _canonical_payload(
    *,
    timestamp: str,
    nonce: str,
    grant_id: str,
    request_id: str,
    body: bytes,
) -> bytes:
    body_hash = hashlib.sha256(body).hexdigest()
    return "\n".join([timestamp, nonce, grant_id, request_id, body_hash]).encode("utf-8")


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthenticationFailed("Invalid MCP timestamp.") from exc
    if parsed.tzinfo is None:
        raise AuthenticationFailed("MCP timestamp must include a timezone.")
    return parsed.astimezone(UTC)


def verify_mcp_hmac(headers, body: bytes) -> VerifiedAgentRequest:
    timestamp = headers.get("X-Mhami-Timestamp", "")
    nonce = headers.get("X-Mhami-Nonce", "")
    grant_id = headers.get("X-Agent-Grant-Id", "")
    request_id = headers.get("X-Request-ID", "")
    signature = _signature_value(headers.get("X-Mhami-Signature", ""))
    if not all([timestamp, nonce, grant_id, request_id, signature]):
        raise AuthenticationFailed("Missing MCP authentication headers.")

    now = datetime.now(UTC)
    age = abs((now - _parse_timestamp(timestamp)).total_seconds())
    if age > settings.MCP_SIGNATURE_TOLERANCE_SECONDS:
        raise AuthenticationFailed("MCP signature timestamp is outside the accepted window.")

    expected = hmac.new(
        str(settings.MCP_INTERNAL_HMAC_SECRET).encode("utf-8"),
        _canonical_payload(
            timestamp=timestamp,
            nonce=nonce,
            grant_id=grant_id,
            request_id=request_id,
            body=body,
        ),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise AuthenticationFailed("Invalid MCP signature.")

    try:
        parsed_request_id = UUID(request_id)
        parsed_grant_id = UUID(grant_id)
    except ValueError as exc:
        raise AuthenticationFailed("Invalid MCP request identifiers.") from exc

    nonce_cache_key = f"mcp:nonce:{grant_id}:{nonce}"
    if not cache.add(nonce_cache_key, "1", timeout=settings.MCP_NONCE_TTL_SECONDS):
        raise AuthenticationFailed("MCP nonce was already used.")

    grant = AgentGrant.objects.select_related("company", "user").filter(id=parsed_grant_id).first()
    if grant is None or not grant.active:
        raise AuthenticationFailed("MCP agent grant is not active.")
    return VerifiedAgentRequest(grant=grant, request_id=parsed_request_id)
