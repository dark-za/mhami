# INFRA-02: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|
| Start Date | YYYY-MM-DD (Phase 1) |
| End Date (Phase 1) | YYYY-MM-DD |
| End Date (Phase 2 — Enforced) | YYYY-MM-DD (after 7-14 day report-only window) |
| Phase | 1 (Report-Only) — Phase 2 (Enforced) is a follow-up PR |
| Number of Commits | N |
| Report-Only header | deployed |
| `<meta>` fallback | deployed |
| `csp-report` view | merged |
| Playwright spec | passed |
| Threat model updated | yes |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String infra\nginx\security-headers.conf -Pattern "Content-Security-Policy"` | 0 matches | — | absent |
| `Select-String frontend\index.html -Pattern "Content-Security-Policy"` | 0 matches | — | absent |
| `Select-String frontend\vite.config.ts -Pattern "nonce"` | 0 matches | — | absent |
| `curl -fsSI http://localhost:3000/ \| Select-String Content-Security-Policy` | 0 matches | — | no header |

### 2.2 Post-Fix (Phase 1)

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String infra\nginx\security-headers.conf -Pattern "Content-Security-Policy-Report-Only"` | 1 match | — | deployed |
| `Select-String infra\nginx\security-headers.conf -Pattern "report-uri"` | 1 match | — | `/api/security/csp-report/` |
| `Select-String frontend\index.html -Pattern "Content-Security-Policy"` | 1 match | — | meta tag |
| `docker compose exec nginx nginx -t` | ok | 0 | syntax clean |
| `curl -fsSI http://localhost:80/ \| Select-String Content-Security-Policy-Report-Only` | 1 match | — | header present |
| `curl -X POST /api/security/csp-report/` | 204 | 0 | view reachable |
| `AuditEvent.objects.filter(event='csp_violation').count()` | ≥ 1 | — | audit row written |
| `pytest apps/security/tests/test_csp_report.py -v` | green | 0 | unit |
| `npx playwright test 07_csp.spec.ts --reporter=line` | 2 passed | 0 | E2E |
| `Select-String docs\SECURITY_THREAT_MODEL.md -Pattern "Content-Security-Policy"` | 1 match | — | threat model updated |

### 2.3 Phase 2 (Enforced — follow-up PR)

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| 0 unintended violations in 7-14 days | TBD | — | review daily |
| `Content-Security-Policy` (enforced) header | TBD | — | after window |
| All existing E2E still green | TBD | — | no regression |

---

## 3. Git Changes

```
<commit-sha-1> INFRA-02: report-only CSP in nginx
  - Add Content-Security-Policy-Report-Only to infra/nginx/security-headers.conf
  - report-uri /api/security/csp-report/

<commit-sha-2> INFRA-02: SPA fallback
  - Add <meta http-equiv="Content-Security-Policy"> to frontend/index.html

<commit-sha-3> INFRA-02: csp-report view
  - Add apps/security/views.py (csp_report)
  - Add apps/security/urls.py
  - Register in config/urls.py
  - Add apps/security/tests/test_csp_report.py

<commit-sha-4> INFRA-02: Playwright spec
  - Add tests/e2e/07_csp.spec.ts (inline + external script blocked)

<commit-sha-5> INFRA-02: docs
  - Update docs/SECURITY_THREAT_MODEL.md
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md

<commit-sha-N> INFRA-02: enforce (follow-up PR after 7-14 days)
  - Replace Content-Security-Policy-Report-Only with Content-Security-Policy
```

---

## 4. Before/After Diff Summary

### `infra/nginx/security-headers.conf` — added Report-Only

```diff
+ add_header Content-Security-Policy-Report-Only "
+   default-src 'self';
+   script-src 'self';
+   style-src 'self' 'unsafe-inline';
+   img-src 'self' data: blob:;
+   font-src 'self' data:;
+   connect-src 'self';
+   frame-ancestors 'none';
+   base-uri 'self';
+   form-action 'self';
+   object-src 'none';
+   upgrade-insecure-requests;
+   report-uri /api/security/csp-report/;
+ " always;
```

### `frontend/index.html` — added meta tag

```diff
+ <meta
+   http-equiv="Content-Security-Policy"
+   content="
+     default-src 'self';
+     script-src 'self';
+     style-src 'self' 'unsafe-inline';
+     img-src 'self' data: blob:;
+     font-src 'self' data:;
+     connect-src 'self';
+     frame-ancestors 'none';
+     base-uri 'self';
+     form-action 'self';
+     object-src 'none';
+     upgrade-insecure-requests;
+   "
+ />
```

### `backend/apps/security/views.py` — new

`csp_report` view that writes a `csp_violation` row to the audit log and returns 204.

### `frontend/tests/e2e/07_csp.spec.ts` — new

Two specs: inline script blocked, external script blocked.

---

## 5. Report-Only Window Log

| Day | Date | Violations | Unintended | Action |
|---|---|---|---|---|
| 0 | YYYY-MM-DD | 0 | 0 | Deploy |
| 1 | | ___ | ___ | Review |
| 2 | | ___ | ___ | Review |
| ... | | ___ | ___ | ... |
| 7 | | ___ | ___ | Decision: enforce? |
| 14 | | ___ | ___ | Final decision |

> **Rule:** 0 unintended violations across 7-14 days → enforce. Any unintended violation → file a defect, fix the legitimate code path, and reset the counter.

---

## 6. Executed Tests and Results

| Test | Result | Duration |
|---|---|---|
| `pytest apps/security/tests/test_csp_report.py` | passed | <1s |
| `curl -X POST /api/security/csp-report/` | 204 | <1s |
| `curl -fsSI http://localhost:80/ \| Select-String Report-Only` | match | <1s |
| `npx playwright test 07_csp.spec.ts` | 2 passed | ~5s |
| `nginx -t` | ok | <1s |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| Invalid JSON in csp-report | 400 | confirmed |
| `csp-report` not reachable | 404 | confirmed (before fix) |
| Playwright spec without the assertion | failure | confirmed (reverted) |

---

## 7. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 8. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| `<meta>` is taken as intersection with the header | The meta is conservative; some browsers may apply the stricter of the two | Document in the meta tag; consider removing the meta after enforcement |
| `csp-report` is unauthenticated | Anyone can flood the audit log | Rate-limit the endpoint; sample the writes |

---

## 9. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete (Phase 1) |
| Security Lead | _________ | _________ | Approved (Phase 1) |
| DevOps Lead | _________ | _________ | Approved (nginx) |
| Frontend Lead | _________ | _________ | Approved (Playwright) |
| Tech Lead | _________ | _________ | Approved |
| Security Lead | _________ | _________ | Approved (Phase 2 — Enforced, after window) |

---

## 10. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
