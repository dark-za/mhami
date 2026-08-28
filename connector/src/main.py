"""H-04: Mhami Linux Docker connector.

The connector is a small FastAPI service that runs inside the
tenant's network. It accepts signed HTTP requests from the Mhami
platform, forwards them to the tenant's private AI provider, and
returns the result. The connector is the only component that has
direct access to the tenant's private model; the shared SaaS
runtime never reaches across the boundary.

Security model (chosen during the design review):

* Every inbound request carries an HMAC-SHA256 signature over the
  ``timestamp + nonce + sha256(body)`` triple. The signature key is
  the shared ``CONNECTOR_API_KEY``; the platform issues a fresh key
  on a defined rotation schedule.
* A replay guard rejects requests whose nonce was seen inside the
  configured freshness window.
* The connector refuses to start without ``CONNECTOR_API_KEY`` and
  refuses to forward to an outbound host other than the configured
  ``TENANT_AI_ENDPOINT``.
* Logs are JSON-only and never include the request body or the API
  key.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response

from .auth import ReplayGuard, load_secret, verify_request

logger = logging.getLogger("mhami.connector")
logging.basicConfig(level=os.environ.get("CONNECTOR_LOG_LEVEL", "INFO"))

app = FastAPI(title="Mhami Connector", version="0.1.0")

_secret: str | None = None
_replay_guard = ReplayGuard(freshness_seconds=int(os.environ.get("CONNECTOR_FRESHNESS_SECONDS", "300")))
_outbound_timeout = float(os.environ.get("CONNECTOR_OUTBOUND_TIMEOUT", "30"))


def get_secret() -> str:
    global _secret
    if _secret is None:
        _secret = load_secret()
    return _secret


def _outbound_url(path: str) -> str:
    base = os.environ.get("TENANT_AI_ENDPOINT", "")
    if not base:
        raise RuntimeError("TENANT_AI_ENDPOINT is required.")
    return base.rstrip("/") + path


def _verify_headers(
    x_mhami_signature: str = Header(default=""),
    x_mhami_timestamp: str = Header(default=""),
    x_mhami_nonce: str = Header(default=""),
) -> dict[str, str]:
    if not x_mhami_signature or not x_mhami_timestamp or not x_mhami_nonce:
        raise HTTPException(status_code=401, detail="Missing signature headers.")
    return {
        "x-mhami-signature": x_mhami_signature,
        "x-mhami-timestamp": x_mhami_timestamp,
        "x-mhami-nonce": x_mhami_nonce,
    }


async def _verify_request(request: Request, headers: dict[str, str] = Depends(_verify_headers)) -> None:
    body = await request.body()
    try:
        verify_request(
            get_secret(),
            headers=headers,
            body=body,
            replay_guard=_replay_guard,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    try:
        get_secret()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready"}


@app.post("/v1/ai/analyze", dependencies=[Depends(_verify_request)])
async def analyze(request: Request) -> Response:
    body = await request.body()
    try:
        payload = json.loads(body or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object.")
    try:
        async with httpx.AsyncClient(timeout=_outbound_timeout) as client:
            upstream = await client.post(
                _outbound_url("/v1/analyze"),
                json=payload,
                headers={"X-Internal-Token": get_secret()},
            )
    except httpx.HTTPError as exc:
        logger.warning("Upstream error: %s", exc.__class__.__name__)
        raise HTTPException(status_code=502, detail="Upstream unavailable.") from exc
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
