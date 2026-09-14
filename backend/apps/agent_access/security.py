from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed

from apps.tenancy.access import is_active_company_user

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
    fingerprint: str,
    body: bytes,
) -> bytes:
    body_hash = hashlib.sha256(body).hexdigest()
    return "\n".join([timestamp, nonce, grant_id, request_id, fingerprint, body_hash]).encode(
        "utf-8"
    )


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
    fingerprint = headers.get("X-Mhami-Client-Fingerprint", "")
    grant_secret = headers.get("X-Mhami-Grant-Secret", "")
    signature = _signature_value(headers.get("X-Mhami-Signature", ""))
    if not all([timestamp, nonce, grant_id, request_id, fingerprint, grant_secret, signature]):
        raise AuthenticationFailed("Missing MCP authentication headers.")

    now = datetime.now(UTC)
    age = abs((now - _parse_timestamp(timestamp)).total_seconds())
    if age > settings.MCP_SIGNATURE_TOLERANCE_SECONDS:
        raise AuthenticationFailed("MCP signature timestamp is outside the accepted window.")

    try:
        parsed_request_id = UUID(request_id)
        parsed_grant_id = UUID(grant_id)
    except ValueError as exc:
        raise AuthenticationFailed("Invalid MCP request identifiers.") from exc

    grant = AgentGrant.objects.select_related("company", "user").filter(id=parsed_grant_id).first()
    if grant is None:
        raise AuthenticationFailed("MCP agent grant not found.")
    if not grant.active:
        raise AuthenticationFailed("MCP agent grant is not active.")

    if not is_active_company_user(grant.company, grant.user):
        raise AuthenticationFailed("MCP grant user has no active company membership.")
    if not hmac.compare_digest(grant.client_fingerprint, fingerprint):
        raise AuthenticationFailed("MCP client fingerprint does not match the grant.")
    if not check_password(grant_secret, grant.secret_hash):
        raise AuthenticationFailed("Invalid MCP grant secret.")

    expected = hmac.new(
        grant_secret.encode("utf-8"),
        _canonical_payload(
            timestamp=timestamp,
            nonce=nonce,
            grant_id=grant_id,
            request_id=request_id,
            fingerprint=fingerprint,
            body=body,
        ),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise AuthenticationFailed("Invalid MCP signature.")

    # Only reserve a nonce after authenticating the request. Otherwise an
    # unauthenticated caller could consume a valid nonce before its client uses it.
    nonce_cache_key = f"mcp:nonce:{grant_id}:{nonce}"
    if not cache.add(nonce_cache_key, "1", timeout=settings.MCP_NONCE_TTL_SECONDS):
        raise AuthenticationFailed("MCP nonce was already used.")

    return VerifiedAgentRequest(grant=grant, request_id=parsed_request_id)
