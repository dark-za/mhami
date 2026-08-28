# INFRA-02: Goal and Plan

## SMART Goal

> Within **2 days**, deploy a **report-only** Content-Security-Policy in
> `infra/nginx/security-headers.conf` (and a matching `<meta>` tag in
> `frontend/index.html`) that blocks `script-src 'self'` and reports
> violations to `/api/security/csp-report/`. After **7-14 days** of
> zero unintended violations, switch the header to **enforced** in a
> follow-up PR.

## Detailed Acceptance Standards

### Standard 1: Policy shape

| Directive | Value | Reason |
|---|---|---|
| `default-src` | `'self'` | baseline deny |
| `script-src` | `'self'` | Vite-built JS, no inline |
| `style-src` | `'self' 'unsafe-inline'` | Vite injects styles |
| `img-src` | `'self' data: blob:` | camera capture, preview images |
| `font-src` | `'self' data:` | web fonts |
| `connect-src` | `'self'` | API + WebSocket on the same origin |
| `frame-ancestors` | `'none'` | replace `X-Frame-Options: DENY` |
| `base-uri` | `'self'` | prevent `<base>` injection |
| `form-action` | `'self'` | keep forms on the same origin |
| `object-src` | `'none'` | block `<object>` / `<embed>` |
| `upgrade-insecure-requests` | (no value) | force HTTPS |
| `report-uri` | `/api/security/csp-report/` | collect violations |

### Standard 2: Two-phase rollout

| Phase | Header | Duration | Exit criterion |
|---|---|---|---|
| 1 | `Content-Security-Policy-Report-Only` | 7-14 days | 0 unintended violations |
| 2 | `Content-Security-Policy` | permanent | enforced |

### Standard 3: SPA fallback

`frontend/index.html` carries a `<meta http-equiv="Content-Security-Policy" content="default-src 'self'; ...">` tag with the same directives. This protects the SPA when nginx is bypassed (e.g. dev) and prevents a regression if a developer serves the built `dist/` with a misconfigured reverse proxy.

### Standard 4: `csp-report` view

`POST /api/security/csp-report/` accepts the standard `application/csp-report` payload:

```json
{
  "csp-report": {
    "document-uri": "https://app.example.com/...",
    "violated-directive": "script-src",
    "blocked-uri": "https://evil.example/x.js",
    "original-policy": "default-src 'self'; ..."
  }
}
```

The view:

1. Validates the JSON shape.
2. Writes a row to the audit log (`event='csp_violation'`).
3. Returns `204 No Content`.

### Standard 5: Playwright spec

`tests/e2e/07_csp.spec.ts` opens a test page that tries to:

- Inject an inline `<script>eval('alert(1)')</script>` — must be blocked.
- Load `<script src="http://evil.example/x.js">` — must be blocked.
- Load an `<img src="https://other.example/x.png">` — must be blocked (or shown as broken).

The spec asserts that `window.__cspViolations.length > 0` after the actions and that the violations are reported to `/api/security/csp-report/`.

### Standard 6: Threat model mapping

`docs/SECURITY_THREAT_MODEL.md` adds a row to the Scanner Matrix (or its replacement) for A05 → CSP.

---

## Detailed Implementation Plan

### Day 1 — Report-Only + SPA fallback + view

**Morning**
- [ ] Add `Content-Security-Policy-Report-Only` to `infra/nginx/security-headers.conf`.
- [ ] Add `<meta http-equiv="Content-Security-Policy">` to `frontend/index.html`.
- [ ] Add the `csp-report` URL in Django (`apps/security/urls.py`).

**Afternoon**
- [ ] Implement the `csp-report` view in `apps/security/views.py`.
- [ ] Write the audit row in the view.
- [ ] Add a unit test (`apps/security/tests/test_csp_report.py`).

### Day 2 — Playwright spec + docs

- [ ] Write `tests/e2e/07_csp.spec.ts`.
- [ ] Run the SPA under nginx and capture a baseline of violations.
- [ ] Update `docs/SECURITY_THREAT_MODEL.md`.
- [ ] Update `CHANGELOG.md`.

### Day 8-15 — Enforce (follow-up PR)

- [ ] After 7-14 days of zero unintended violations, change the header to `Content-Security-Policy` (enforced).
- [ ] Remove the `<meta>` tag if it conflicts with the enforced header (browsers take the **intersection** of header + meta, so keeping the meta is conservative).

---

## Dependency Graph

```
nginx + meta + view (Day 1)
    ↓
Playwright spec (Day 2)
    ↓
7-14 day report-only window
    ↓
Enforce (Day 8-15, follow-up PR)
    ↓
docs + CHANGELOG
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Report-Only header merged | DevOps |
| CP-2 | `<meta>` tag merged | Frontend |
| CP-3 | `csp-report` view merged | Backend |
| CP-4 | Playwright spec green | Frontend |
| CP-5 | Zero unintended violations in 7-14 days | DevOps |
| CP-6 | Enforced header merged (follow-up PR) | DevOps |
| CP-7 | Threat model updated | Security Lead |
| CP-8 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If the report-only window reveals a legitimate violation that cannot be fixed → add a narrow exception in the policy (e.g. `script-src 'self' https://specific.cdn.example`) and document in `docs/SECURITY_EXCEPTIONS.md`. Do not relax the global policy.
- If the `csp-report` endpoint overwhelms the audit log → rate-limit and sample; keep the endpoint, drop the writes.
