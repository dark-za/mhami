"""H-03 regression tests: real OpenAI provider.

The provider refuses to instantiate without an allowlist match or an
API key, and re-validates the structured output returned by the
upstream. We use ``respx``-style monkey-patching via ``unittest.mock``
to keep the test suite hermetic.
"""

from __future__ import annotations

from unittest import mock

import pytest

from apps.ai_gateway.providers import (
    OpenAIProvider,
    validate_provider_result,
)

pytestmark = pytest.mark.django_db


def test_provider_rejects_endpoint_outside_allowlist():
    with pytest.raises(ValueError):
        OpenAIProvider(
            endpoint_url="https://malicious.example.com",
            api_key="sk-test",
            model_name="gpt-4o-mini",
            allowlist=["api.openai.com"],
        )


def test_provider_requires_api_key():
    with pytest.raises(ValueError):
        OpenAIProvider(
            endpoint_url="https://api.openai.com",
            api_key="",
            model_name="gpt-4o-mini",
            allowlist=["api.openai.com"],
        )


def test_provider_sends_request_and_parses_response():
    fake_response = mock.Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"verdict": "approve", "risk_level": "low", "confidence": 90, "explanation": "ok", "auto_pass_eligible": false}'
                }
            }
        ]
    }
    fake_post = mock.Mock(return_value=fake_response)
    fake_client = mock.MagicMock()
    fake_client.__enter__.return_value.post = fake_post
    fake_client.__exit__.return_value = False
    with mock.patch("httpx.Client", return_value=fake_client):
        provider = OpenAIProvider(
            endpoint_url="https://api.openai.com",
            api_key="sk-test",
            model_name="gpt-4o-mini",
            allowlist=["api.openai.com"],
        )
        result = provider.analyze(
            evidence_summary={"duplicate_risk_score": 10, "face_detected": False},
            criteria={"auto_pass_enabled": True},
        )
    assert result["verdict"] == "approve"
    assert fake_post.call_args.kwargs["json"]["model"] == "gpt-4o-mini"


def test_provider_rejects_malformed_response():
    fake_response = mock.Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"choices": [{"message": {"content": "not json"}}]}
    fake_post = mock.Mock(return_value=fake_response)
    fake_client = mock.MagicMock()
    fake_client.__enter__.return_value.post = fake_post
    fake_client.__exit__.return_value = False
    with mock.patch("httpx.Client", return_value=fake_client):
        provider = OpenAIProvider(
            endpoint_url="https://api.openai.com",
            api_key="sk-test",
            model_name="gpt-4o-mini",
            allowlist=["api.openai.com"],
        )
        with pytest.raises(ValueError):
            provider.analyze(
                evidence_summary={"duplicate_risk_score": 0},
                criteria={},
            )


def test_validate_provider_result_rejects_invalid_verdict():
    with pytest.raises(ValueError):
        validate_provider_result({"verdict": "bogus", "risk_level": "low", "confidence": 50, "explanation": "x"})
