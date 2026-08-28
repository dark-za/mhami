"""AI provider implementations used by the AI gateway.

The platform supports two provider backends out of the box:

* :class:`FakeProvider` — deterministic, no network access. Used in
  tests and in environments where egress is not yet approved.
* :class:`OpenAIProvider` — OpenAI-compatible Chat Completions client
  (works with OpenAI, Azure OpenAI, vLLM, and any other endpoint that
  implements the same protocol).

H-03: the OpenAI client is intentionally strict. The endpoint URL
must be in the ``AI_PROVIDER_ALLOWED_ENDPOINTS`` allowlist, the
secret is resolved from ``AI_PROVIDER_API_KEY`` (never from the
request), and every request carries a strict timeout, a JSON response
format, and a structured-output schema that is re-validated server
side. A missing allowlist, an empty secret, a non-200 response, a
JSON-decode error, a schema mismatch, or an HTTP timeout are all
treated as a hard error that the gateway surfaces as a 4xx without
leaking the upstream payload.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_provider_result(result: dict[str, Any]) -> dict[str, Any]:
    verdict = result.get("verdict")
    risk_level = result.get("risk_level")
    confidence = result.get("confidence")
    explanation = result.get("explanation")
    if verdict not in {"approve", "review", "reject"}:
        raise ValueError("Invalid provider verdict.")
    if risk_level not in {"low", "medium", "high"}:
        raise ValueError("Invalid provider risk level.")
    if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
        raise ValueError("Invalid provider confidence.")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError("Provider explanation is required.")
    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "confidence": confidence,
        "explanation": explanation,
        "auto_pass_eligible": bool(result.get("auto_pass_eligible", False)),
    }


SYSTEM_PROMPT = (
    "You are an evidence-review assistant for the Mhami platform. "
    "You must respond with a single JSON object matching the schema: "
    "{verdict: approve|review|reject, risk_level: low|medium|high, "
    "confidence: integer 0-100, explanation: string, auto_pass_eligible: boolean}. "
    "Do not include any prose outside the JSON object."
)


def _is_allowed_endpoint(endpoint: str, allowlist: list[str]) -> bool:
    """Return True iff ``endpoint`` is a same-host match against any allowlist entry."""
    if not endpoint or not allowlist:
        return False
    try:
        target = urlparse(endpoint)
    except ValueError:
        return False
    if target.scheme not in {"http", "https"} or not target.hostname:
        return False
    for entry in allowlist:
        try:
            candidate = urlparse(entry)
        except ValueError:
            continue
        if candidate.hostname and candidate.hostname == target.hostname:
            return True
    return False


class FakeProvider:
    slug = "fake"

    def analyze(self, *, evidence_summary: dict[str, Any], criteria: dict[str, Any]) -> dict[str, Any]:
        duplicate_risk = int(evidence_summary.get("duplicate_risk_score", 0) or 0)
        face_detected = bool(evidence_summary.get("face_detected", False))
        threshold = int(criteria.get("auto_pass_risk_threshold", 70) or 70)
        if duplicate_risk >= threshold:
            return {
                "verdict": "review",
                "risk_level": "high",
                "confidence": max(10, 100 - duplicate_risk),
                "explanation": "Duplicate-risk threshold exceeded.",
                "auto_pass_eligible": False,
            }
        if face_detected:
            return {
                "verdict": "review",
                "risk_level": "medium",
                "confidence": 72,
                "explanation": "Face derivative requires review.",
                "auto_pass_eligible": False,
            }
        return {
            "verdict": "approve",
            "risk_level": "low",
            "confidence": 92,
            "explanation": "Evidence is within expected bounds.",
            "auto_pass_eligible": bool(criteria.get("auto_pass_enabled", False)),
        }


class OpenAIProvider:
    """OpenAI-compatible Chat Completions provider.

    H-03: the provider refuses to start if the endpoint is not in the
    allowlist or the API key is empty. The chat-completions call uses
    the strict ``response_format={"type": "json_object"}`` mode and a
    short timeout so a slow upstream cannot wedge a worker. Errors are
    logged with a redacted message and re-raised as ``ValueError`` so
    the gateway surfaces a clean 4xx without leaking the upstream
    payload.
    """

    slug = "openai"

    def __init__(self, *, endpoint_url: str, api_key: str, model_name: str, allowlist: list[str], timeout_seconds: int = 15):
        if not _is_allowed_endpoint(endpoint_url, allowlist):
            raise ValueError("AI provider endpoint is not in the allowlist.")
        if not api_key:
            raise ValueError("AI provider API key is required.")
        if not model_name:
            raise ValueError("AI provider model name is required.")
        self.endpoint_url = endpoint_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = max(1, int(timeout_seconds))

    def analyze(self, *, evidence_summary: dict[str, Any], criteria: dict[str, Any]) -> dict[str, Any]:
        import httpx

        user_prompt = json.dumps(
            {
                "evidence_summary": evidence_summary,
                "criteria": criteria,
            },
            sort_keys=True,
            default=str,
        )
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.endpoint_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.0,
                    },
                )
        except httpx.HTTPError as exc:
            logger.warning("AI provider request failed: %s", exc.__class__.__name__)
            raise ValueError("AI provider request failed.") from exc
        if response.status_code != 200:
            logger.warning("AI provider returned %s", response.status_code)
            raise ValueError("AI provider returned a non-success response.")
        try:
            payload = response.json()
            message = payload["choices"][0]["message"]["content"]
            parsed = json.loads(message)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ValueError("AI provider response could not be parsed.") from exc
        return validate_provider_result(parsed)


def build_provider(config) -> "FakeProvider | OpenAIProvider":
    """Return a provider instance for the given configuration.

    H-03: provider selection is server-side. A request that names a
    provider not present in the registry raises an error before any
    network call is made.
    """
    provider_name = (getattr(config, "provider_name", "") or "").lower()
    if provider_name in {"", "fake"}:
        return FakeProvider()
    if provider_name == "openai":
        from django.conf import settings as django_settings

        allowlist = list(getattr(django_settings, "AI_PROVIDER_ALLOWED_ENDPOINTS", []) or [])
        return OpenAIProvider(
            endpoint_url=config.endpoint_url,
            api_key=getattr(django_settings, "AI_PROVIDER_API_KEY", "") or "",
            model_name=config.model_name,
            allowlist=allowlist,
            timeout_seconds=getattr(django_settings, "AI_PROVIDER_TIMEOUT_SECONDS", 15),
        )
    raise ValueError(f"Unknown AI provider '{provider_name}'.")
