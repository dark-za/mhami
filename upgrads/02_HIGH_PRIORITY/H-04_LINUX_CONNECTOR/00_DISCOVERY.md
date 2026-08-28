# H-04: Linux Docker Connector Implementation

> **Gate C only.** The connector must not receive personal data or be enrolled
> by a pilot until Gate B approvals, approved data flows, and egress controls
> exist. Prefer a tenant-initiated outbound connection over an internet-exposed
> inbound service.

## Discovery

### Problem
The `connector/` folder contains only `README.md`. There is no runnable connector code.

### Evidence
```bash
$ ls -la connector/
-rw-r--r-- 1 user user 1.2K README.md
```

### Impact
- The "Tenant Connector" claim is empty
- No private AI integration
- No local-first deployment

### Security design constraints

The sample below is not an approved implementation. A value called
`PLATFORM_PUBLIC_KEY` cannot safely serve as an HMAC secret. HMAC requires a
secret shared only by the two parties; the example also lacks timestamp-window
validation, replay storage, request-body binding, mTLS/service identity, tenant
binding, network policy, and outbound allowlisting.

The design review must choose one protocol before implementation:

1. Tenant connector opens an outbound mutually authenticated channel to the
   platform and polls/receives signed jobs; or
2. A narrowly exposed inbound endpoint with mTLS, private networking, replay
   protection, body digest signatures, and an explicit tenant identity.

### Illustrative structure only

**New Structure:**
```
connector/
├── README.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py            # FastAPI app
│   ├── auth.py            # HMAC signature
│   ├── health.py
│   ├── ai_proxy.py        # proxies to tenant AI
│   └── jobs.py            # async job execution
├── tests/
│   ├── test_auth.py
│   ├── test_ai_proxy.py
│   └── test_health.py
└── config/
    └── example.env
```

**Core Code:** `connector/src/main.py`

```python
"""Linux Docker Connector for Mhami Platform.

Receives authenticated requests from the platform, forwards to tenant's
private AI provider, and returns results. The connector NEVER exposes
the tenant's private network to the shared platform.
"""
from fastapi import FastAPI, Header, HTTPException, Depends
import httpx
import hmac
import hashlib
import os

app = FastAPI(title="Mhami Connector")

API_KEY = os.environ["CONNECTOR_API_KEY"]
PLATFORM_PUBLIC_KEY = os.environ["PLATFORM_PUBLIC_KEY"]
TENANT_AI_ENDPOINT = os.environ["TENANT_AI_ENDPOINT"]


def verify_platform_signature(
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    x_request_id: str = Header(...),
):
    """Verify the request came from the platform."""
    expected = hmac.new(
        PLATFORM_PUBLIC_KEY.encode(),
        f"{x_request_id}:{x_timestamp}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(x_signature, expected):
        raise HTTPException(401, "Invalid signature")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/ai/analyze")
def analyze(
    payload: dict,
    _auth=Depends(verify_platform_signature),
):
    """Forward analyze request to tenant AI."""
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{TENANT_AI_ENDPOINT}/v1/analyze",
            json=payload,
            headers={"X-Internal-Token": API_KEY},
        )
    return response.json()
```

**Dockerfile:**

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Acceptance Criteria
- AC-1: Threat model and ADR select the connection direction and identity model.
- AC-2: Connector and platform bind every job to one tenant, request ID, body
  digest, timestamp window, nonce, and replay record.
- AC-3: mTLS or an approved equivalent, secret rotation, revocation, outbound
  allowlists, timeout, queue backpressure, and kill switch are implemented.
- AC-4: Container runs non-root with no Docker socket, minimal egress, health,
  readiness, and signed release artifact.
- AC-5: Integration tests cover replay, expired timestamp, altered body,
  revoked credential, tenant mismatch, upstream outage, queue retry, and
  network denial using synthetic data.
- AC-6: Security and Privacy approve the data flow before real data is enabled.

### Tests
```python
def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_analyze_requires_signature():
    response = client.post("/v1/ai/analyze", json={})
    assert response.status_code == 401

def test_analyze_with_valid_signature():
    headers = generate_valid_headers()
    response = client.post("/v1/ai/analyze", json={...}, headers=headers)
    assert response.status_code == 200
```
