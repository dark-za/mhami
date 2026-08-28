# INFRA-02: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. CSP is rolled out in two phases (Report-Only, then Enforced) — never skip the report-only window.

## Step 1: Add `Content-Security-Policy-Report-Only` to nginx

### 1.1 File before — `infra/nginx/security-headers.conf`

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "same-origin" always;
add_header Permissions-Policy "geolocation=(), camera=(), microphone=()" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 1.2 File after

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "same-origin" always;
add_header Permissions-Policy "geolocation=(), camera=(), microphone=()" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
# INFRA-02 Phase 1: report-only CSP. After 7-14 days of zero unintended
# violations, change this to a strict `Content-Security-Policy` header.
add_header Content-Security-Policy-Report-Only "
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob:;
  font-src 'self' data:;
  connect-src 'self';
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
  object-src 'none';
  upgrade-insecure-requests;
  report-uri /api/security/csp-report/;
" always;
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx nginx -t
# Expected: "syntax is ok"

docker compose -f compose.yml -f compose.prod.yml restart nginx
curl -fsSI http://localhost:80/ | Select-String -Pattern "Content-Security-Policy-Report-Only"
# Expected: 1 match
```

---

## Step 2: Add `<meta>` fallback to `frontend/index.html`

### 2.1 File before

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Mhami</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### 2.2 File after

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <!--
      INFRA-02: meta-tag fallback for the CSP. When the SPA is served by a
      reverse proxy that does not add the header (e.g. local dev), the
      browser still enforces the same policy.
    -->
    <meta
      http-equiv="Content-Security-Policy"
      content="
        default-src 'self';
        script-src 'self';
        style-src 'self' 'unsafe-inline';
        img-src 'self' data: blob:;
        font-src 'self' data:;
        connect-src 'self';
        frame-ancestors 'none';
        base-uri 'self';
        form-action 'self';
        object-src 'none';
        upgrade-insecure-requests;
      "
    />
    <title>Mhami</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Verify:**
```bash
Select-String -Path frontend\index.html -Pattern "Content-Security-Policy"
# Expected: 1 match
```

---

## Step 3: `csp-report` view

### 3.1 New file: `backend/apps/security/__init__.py`

```python
"""Cross-cutting security views (CSP reports, etc.)."""
```

### 3.2 New file: `backend/apps/security/views.py`

```python
"""Cross-cutting security views.

INFRA-02: the ``csp_report`` view accepts violation reports sent by the
browser when the report-only CSP header is hit. The view is intentionally
permissive in shape (the browser payload is documented but not strictly
typed) and writes a single row to the audit log.
"""
from __future__ import annotations

import json
import logging

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

log = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def csp_report(request: HttpRequest) -> HttpResponse:
    """Accept a CSP violation report and audit it."""
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    report = payload.get("csp-report") or payload
    if not isinstance(report, dict):
        return HttpResponse(status=400)

    # Lazy import: avoid importing the audit model on every request.
    from apps.audit.services import write_audit_event

    write_audit_event(
        event="csp_violation",
        actor=None,  # system
        context={
            "document_uri": report.get("document-uri", ""),
            "violated_directive": report.get("violated-directive", ""),
            "blocked_uri": report.get("blocked-uri", ""),
            "original_policy": report.get("original-policy", ""),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        },
    )
    return HttpResponse(status=204)
```

### 3.3 New file: `backend/apps/security/urls.py`

```python
from django.urls import path

from . import views

urlpatterns = [
    path("csp-report/", views.csp_report, name="csp-report"),
]
```

### 3.4 Register in the project URLs — `backend/config/urls.py`

```python
urlpatterns = [
    # ... existing patterns ...
    path("api/security/", include("apps.security.urls")),
]
```

**Verify:**
```bash
curl -fsS -X POST http://localhost:8000/api/security/csp-report/ -H "Content-Type: application/csp-report" -d '{"csp-report": {"violated-directive": "script-src", "blocked-uri": "https://evil.example/x.js"}}'
echo "Exit code: $LASTEXITCODE"
# Expected: 204
```

---

## Step 4: `write_audit_event` helper

If `apps.audit.services.write_audit_event` does not exist, add a thin wrapper that creates an `AuditEvent` row:

```python
# backend/apps/audit/services.py
from apps.audit.models import AuditEvent

def write_audit_event(*, event: str, actor=None, context: dict) -> AuditEvent:
    return AuditEvent.objects.create(
        event=event,
        actor=actor,
        context=context,
    )
```

---

## Step 5: Unit test — `apps/security/tests/test_csp_report.py`

```python
"""CSP report endpoint."""
from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.django_db


def test_csp_report_writes_audit_row(client):
    payload = {
        "csp-report": {
            "document-uri": "https://app.example.com/",
            "violated-directive": "script-src 'self'",
            "blocked-uri": "https://evil.example/x.js",
            "original-policy": "default-src 'self'; script-src 'self';",
        }
    }
    res = client.post(
        "/api/security/csp-report/",
        data=json.dumps(payload),
        content_type="application/csp-report",
    )
    assert res.status_code == 204

    from apps.audit.models import AuditEvent
    assert AuditEvent.objects.filter(event="csp_violation").count() == 1


def test_csp_report_invalid_json_returns_400(client):
    res = client.post(
        "/api/security/csp-report/",
        data=b"not json",
        content_type="application/csp-report",
    )
    assert res.status_code == 400
```

**Verify:**
```bash
cd backend
pytest apps/security/tests/test_csp_report.py -v
# Expected: 2 passed
```

---

## Step 6: Playwright spec — `frontend/tests/e2e/07_csp.spec.ts`

```ts
import { test, expect } from "@playwright/test";
import { login } from "./_helpers/auth";

test.describe("Content-Security-Policy", () => {
  test("inline script is blocked", async ({ page }) => {
    const violations: { directive: string; blockedUri: string }[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error" && /Content Security Policy/.test(msg.text())) {
        violations.push({ directive: "inline", blockedUri: "inline" });
      }
    });

    await login(page, "owner");
    // Inject a forbidden inline script
    await page.evaluate(() => {
      const s = document.createElement("script");
      s.textContent = "window.__cspInjected = true;";
      document.body.appendChild(s);
    });

    // The variable must not be set
    const injected = await page.evaluate(() => (window as any).__cspInjected);
    expect(injected).toBeUndefined();
    // At least one violation was reported
    expect(violations.length).toBeGreaterThan(0);
  });

  test("external script is blocked", async ({ page }) => {
    const violations: string[] = [];
    page.on("requestfailed", (req) => {
      if (req.resourceType() === "script") violations.push(req.url());
    });

    await login(page, "owner");
    await page.evaluate(() => {
      const s = document.createElement("script");
      s.src = "https://evil.example/x.js";
      document.body.appendChild(s);
    });
    await page.waitForTimeout(500);
    expect(violations).toContain("https://evil.example/x.js");
  });
});
```

**Verify:**
```bash
cd frontend
npx playwright test tests/e2e/07_csp.spec.ts --reporter=line
# Expected: 2 passed
```

---

## Step 7: Threat model update

Append to `docs/SECURITY_THREAT_MODEL.md`:

```markdown
| A05 Security Misconfiguration | CSP (Report-Only → Enforced) + ZAP | nginx + compose |
```

**Verify:**
```bash
Select-String -Path docs\SECURITY_THREAT_MODEL.md -Pattern "Content-Security-Policy"
# Expected: 1 match
```

---

## Step 8: Documentation

1. Update `docs/SECURITY_THREAT_MODEL.md` (CSP row).
2. Update `CHANGELOG.md` with an `INFRA-02` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Report-Only in nginx | `grep Content-Security-Policy-Report-Only infra/nginx/security-headers.conf` | match |
| Meta in index.html | `grep Content-Security-Policy frontend/index.html` | match |
| View reachable | `curl -X POST /api/security/csp-report/` | 204 |
| Audit row written | `AuditEvent.objects.filter(event='csp_violation').count()` | ≥ 1 |
| Playwright spec | `npx playwright test 07_csp.spec.ts` | passed |
| nginx config valid | `nginx -t` | ok |
| Threat model | `grep "Content-Security-Policy" docs/SECURITY_THREAT_MODEL.md` | match |

---

## Rollback

```bash
git revert <infra02-commit-sha>
docker compose -f compose.yml -f compose.prod.yml restart nginx
# The Report-Only header is removed; the SPA behaves as before.
```

> **Important:** Do **not** enforce the policy in Phase 1. Always roll back the header change, not the SPA fallback.
