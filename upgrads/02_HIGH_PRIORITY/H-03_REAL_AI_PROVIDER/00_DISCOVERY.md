# H-03: Implement Real AI Provider

> **Gate C only.** Do not implement or enable external personal-data egress
> until Gate B has Legal, Privacy, Security, data-classification, DPIA, and
> approved transfer evidence. Before that gate, this work is limited to mocks,
> contract tests, and synthetic or documented anonymized data.

## Discovery

### Problem
`backend/apps/ai_gateway/providers.py:25-60` contains only `FakeProvider`. `openai==1.60.0` is installed in requirements.txt but is not used.

### Evidence
```bash
$ grep -r "openai\." backend/apps/ai_gateway/
# 0 Results

$ ls backend/apps/ai_gateway/
# only providers.py, services.py, models.py
```

### Impact
- "AI Gateway" claim is empty
- No real completion with OpenAI/Anthropic/local
- Pilot/Production does not work in practice

### Design constraints

The illustrative implementation below is not production-ready by itself.
`startswith` is not a safe endpoint allowlist, an arbitrary endpoint must not
be accepted from a tenant request, and `api_key_ref` must be resolved only by a
server-side secret manager. The provider must have an egress policy, DNS/IP
revalidation, timeout/retry/circuit-breaker behavior, structured-output limits,
redacted errors, budget enforcement, kill switch, and audit telemetry.

### Illustrative interface only

**File:** `backend/apps/ai_gateway/providers.py` (Add)

```python
import httpx
from typing import Any

class OpenAIProvider:
    """OpenAI-compatible provider (works with OpenAI, Azure, local vLLM, etc.)."""

    slug = "openai"

    def __init__(self, config: dict[str, Any]):
        self.endpoint = config["endpoint_url"]
        self.api_key = config["api_key_ref"]  # resolved from vault
        self.model = config["model_name"]
        self.timeout = config.get("timeout_seconds", 30)

    def analyze(
        self,
        *,
        evidence_summary: dict[str, Any],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        # Allowlist endpoints
        if not self._is_allowed_endpoint():
            raise ValueError("Endpoint not in allowlist")

        prompt = self._build_prompt(evidence_summary, criteria)

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.endpoint}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.0,
                },
            )

        if response.status_code != 200:
            raise ValueError(f"Provider error: {response.status_code}")

        result = response.json()
        return validate_provider_result(result["choices"][0]["message"]["parsed"])

    def _is_allowed_endpoint(self) -> bool:
        from django.conf import settings
        allowed = settings.AI_PROVIDER_ALLOWED_ENDPOINTS
        return any(self.endpoint.startswith(a) for a in allowed)
```

### Acceptance Standards
- AC-1: A provider configuration can reference only an approved provider ID and
  server-owned endpoint profile; users cannot submit arbitrary URLs.
- AC-2: Secrets remain in a secret manager and are never serialized, logged, or
  returned to the browser.
- AC-3: `validate_provider_result`, strict size/schema limits, timeout, retry,
  circuit-breaker, budget, and shadow-only controls are enforced.
- AC-4: Contract, egress-denial, timeout, malformed-result, budget, kill-switch,
  and redaction tests pass using synthetic data.
- AC-5: Legal/Privacy/Security approve the data flow before any non-synthetic
  request; owner acceptance alone is not a substitute.

### Tests
```python
def test_openai_provider_sends_request():
    with mock.patch("httpx.Client.post") as mock_post:
        mock_post.return_value = mock_response(...)
        provider = OpenAIProvider({...})
        result = provider.analyze(...)
        assert result["verdict"] == "approve"

def test_openai_provider_rejects_invalid_endpoint():
    provider = OpenAIProvider({"endpoint_url": "https://malicious.com", ...})
    with pytest.raises(ValueError):
        provider.analyze(...)

def test_openai_provider_validates_output():
    with mock.patch("httpx.Client.post") as mock_post:
        mock_post.return_value = mock_response({"verdict": "invalid"})
        provider = OpenAIProvider({...})
        with pytest.raises(ValueError):
            provider.analyze(...)
```
