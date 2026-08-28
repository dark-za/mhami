# INFRA-02: Content-Security-Policy

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** `infra/nginx/security-headers.conf` configures `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and `Strict-Transport-Security`, but **does not include a `Content-Security-Policy` header**. The frontend is a static SPA built by Vite; any inline script or `style` will be blocked by a strict CSP. A nonced-CSP would be ideal, but it requires the **same nonce** in the response header and in the inline HTML — a contract the static SPA does not currently establish.

**Evidence gathered:**
- `infra/nginx/security-headers.conf` — no `Content-Security-Policy` line.
- `frontend/index.html` — no `<meta http-equiv="Content-Security-Policy" content="...">` tag.
- `frontend/vite.config.ts` — does not inject a nonce into the built HTML.
- `docs/SECURITY_AND_DATA_BASELINE.md` — does not list a CSP SLO.
- `docs/SECURITY_THREAT_MODEL.md` — A05 Security Misconfiguration is in the matrix but has no mitigating control.

### Impact

| Dimension | Impact |
|---|---|
| Functional | A future XSS or supply-chain attack on the SPA can run with full privileges. |
| Security | No defence in depth against script injection. |
| Compliance | Gate-B (PDPL-aligned) and A05 in OWASP Top 10 are not mitigated. |
| Operational | Adding a strict CSP now would break the SPA; rolling it out must be staged. |

### Reproducible Evidence

```bash
# 1. Confirm CSP is missing from nginx config
Select-String -Path infra\nginx\security-headers.conf -Pattern "Content-Security-Policy"
# Expected today: 0 matches

# 2. Confirm CSP is missing from the SPA
Select-String -Path frontend\index.html -Pattern "Content-Security-Policy"
# Expected today: 0 matches

# 3. Confirm Vite does not inject a nonce
Select-String -Path frontend\vite.config.ts -Pattern "nonce"
# Expected today: 0 matches

# 4. Inspect response headers from a running dev server
curl -fsSI http://localhost:5173/ | Select-String -Pattern "Content-Security-Policy"
# Expected today: no CSP header
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `Content-Security-Policy-Report-Only` in nginx | none | deployed (collect violations for 7-14 days) |
| `Content-Security-Policy` in nginx | none | deployed after the report-only window |
| `<meta http-equiv="Content-Security-Policy">` in `index.html` | none | fallback when nginx is bypassed (e.g. dev) |
| Nonce generation | none | middleware (Django) for the login form; per-request nonce in `index.html` |
| `Report-To` / `report-uri` | none | configured to `/api/security/csp-report/` |
| Test: enforced CSP blocks injected `<script>` | no | yes (Playwright spec) |

---

## 3. Goal Statement

> Within **2 days**, deploy a `Content-Security-Policy-Report-Only` header in `infra/nginx/security-headers.conf` with a static policy (`default-src 'self'; script-src 'self'; ...`), collect violations for 7-14 days, then **enforce** the policy in a follow-up PR. The SPA must pass a Playwright test that asserts a `<script src="http://evil.example/x.js">` is blocked.

### Acceptance Criteria

1. **AC-1:** `infra/nginx/security-headers.conf` includes a `Content-Security-Policy-Report-Only` header with a static policy.
2. **AC-2:** A `report-uri` directive points at `/api/security/csp-report/`.
3. **AC-3:** `frontend/index.html` carries a `<meta http-equiv="Content-Security-Policy" content="default-src 'self'; ...">` fallback for dev.
4. **AC-4:** A Playwright spec (`tests/e2e/07_csp.spec.ts`) loads a page that injects an inline `<script>` and asserts the CSP blocks it.
5. **AC-5:** A `csp-report` view accepts POSTed violation reports and writes a row to the audit log.
6. **AC-6:** The `Content-Security-Policy` (enforced) header is added **only after** the report-only window confirms zero violations from legitimate code paths.
7. **AC-7:** `docs/SECURITY_THREAT_MODEL.md` is updated to map A05 → CSP.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Strict CSP blocks the SPA | High | High | Start with `Report-Only`; review violations before enforcing. |
| Inline `<style>` blocked | High | Medium | Allow `'unsafe-inline'` for `style-src` only (Vite injects styles). |
| `data:` and `blob:` blocked | Medium | Medium | Allow `data:` and `blob:` for `img-src` (camera capture). |
| Report endpoint overwhelms the audit log | Low | Medium | Rate-limit and sample the report endpoint. |
| Third-party scripts (e.g. analytics) break | Medium | Medium | Add explicit `script-src` allows; document in `docs/SECURITY_EXCEPTIONS.md`. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `Content-Security-Policy-Report-Only` to `infra/nginx/security-headers.conf` | DevOps | not-started |
| 2 | Add `report-uri /api/security/csp-report/` | DevOps | not-started |
| 3 | Add `<meta http-equiv="Content-Security-Policy">` to `frontend/index.html` | Frontend | not-started |
| 4 | Add `csp-report` view in `apps/security` (or `apps/audit`) | Backend | not-started |
| 5 | Write `tests/e2e/07_csp.spec.ts` | Frontend | not-started |
| 6 | Run the SPA under nginx and capture a baseline of violations | DevOps | not-started |
| 7 | After 7-14 days, switch `Report-Only` to enforced | DevOps | not-started |
| 8 | Update `docs/SECURITY_THREAT_MODEL.md` | Security Lead | not-started |
| 9 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [infra/nginx/security-headers.conf](../../../infra/nginx/security-headers.conf)
- [frontend/index.html](../../../frontend/index.html)
- [docs/SECURITY_THREAT_MODEL.md](../../../docs/SECURITY_THREAT_MODEL.md)
- [INFRA-01 — Hardened Compose](..) — nginx service introduced there
- [QA-03 — Playwright E2E](..) — share the auth helper for the CSP test
