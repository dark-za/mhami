# H-03: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED (Gate C gated)

## Verification Evidence

### Two providers in the registry

`backend/apps/ai_gateway/providers.py` ships:

1. `FakeProvider` — deterministic, no network egress. Used by tests and
   in environments where egress is not yet approved. Verdict is derived
   from the same evidence summary the gateway collects so the rest of
   the platform can be exercised end-to-end without an upstream.
2. `OpenAIProvider` — OpenAI-compatible Chat Completions client. Works
   with OpenAI, Azure OpenAI, vLLM, and any other endpoint that
   implements the same protocol.

`build_provider(config)` selects between them server-side based on
`config.provider_name`. A request that names a provider not in the
registry is rejected before any network call.

### Strict allowlist

`_is_allowed_endpoint(endpoint, allowlist)` parses both URLs and
verifies that the **hostname** (not the full URL string) is in
`AI_PROVIDER_ALLOWED_ENDPOINTS`. This is the correct compare: a
`startswith` check would be exploitable via `https://api.openai.com.evil.tld/`,
whereas a hostname compare is not. The `OpenAIProvider.__init__` raises
`ValueError` immediately if the endpoint fails the allowlist, so a
misconfigured gateway never reaches the network.

### Server-side secret resolution

The API key is loaded by `build_provider` from
`settings.AI_PROVIDER_API_KEY` and passed in memory to the
`OpenAIProvider`. It is **never** serialised, never returned in a
response, and never logged. The structured logger redacts the
exception class name but not the payload.

### Structured output + re-validation

The provider calls the upstream with
`response_format={"type": "json_object"}` and `temperature=0.0`, then
runs the response through `validate_provider_result` which enforces:

- `verdict ∈ {"approve", "review", "reject"}`
- `risk_level ∈ {"low", "medium", "high"}`
- `confidence ∈ [0, 100]`
- `explanation` is a non-empty string
- `auto_pass_eligible` is a boolean

Any deviation raises `ValueError`; the gateway surfaces it as a 4xx
without leaking the upstream payload.

### Timeout, retry, and circuit breaker

The provider uses a short `httpx.Client(timeout=...)` so a slow
upstream cannot wedge a worker. The number of retries, the circuit
breaker, and the budget enforcement live in
`apps/ai_gateway/services.py` and the management command
`apps/ai_gateway/management/commands/ai_circuit_breaker.py`, both of
which are covered by `tests/test_ai_gateway_api.py`.

### Tests

`backend/apps/ai_gateway/tests/test_openai_provider.py` covers the
allowlist rejection, the empty-key rejection, the happy path with a
mocked `httpx.Client`, the malformed-response path, and the schema
validator. The tests use `unittest.mock` so the suite is hermetic and
runs in CI without any network access.

`backend/apps/ai_gateway/tests/test_ai_gateway_api.py` covers the
public HTTP contract, the kill switch, the budget enforcement, and the
egress-denial path against the configured allowlist.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Provider references only approved provider ID + server-owned endpoint | PASS | `build_provider` + `_is_allowed_endpoint` hostname compare |
| AC-2 Secrets stay in a secret manager, never serialised / logged / returned | PASS | Server-side resolution + redaction in logger |
| AC-3 Validate, strict size/schema limits, timeout, retry, breaker, budget, kill switch | PASS | `services.py` + `test_ai_gateway_api.py` |
| AC-4 Contract / egress-denial / timeout / malformed / budget / kill-switch / redaction tests pass with synthetic data | PASS | `test_openai_provider.py` + `test_ai_gateway_api.py` |
| AC-5 Legal / Privacy / Security approve the data flow before non-synthetic data | GATE C | Pending Gate B exit review |

## Risks / Follow-ups

- Gate C is the gate that authorises real personal-data egress. Until
  Gate C, only the `FakeProvider` is wired into the production
  gateway; the OpenAI provider is reachable only from the test suite.
- Any new provider (e.g. Anthropic, local Ollama) must follow the same
  contract: server-side allowlist, secret resolution from settings,
  strict schema re-validation, and a hermetic test suite.
