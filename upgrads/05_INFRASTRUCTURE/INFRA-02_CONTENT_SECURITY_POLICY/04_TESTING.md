# INFRA-02: Test Strategy

> **Rule:** every test in this file must run against a real backend + nginx; the **Playwright spec is the gate** for moving from Report-Only to Enforced.

## 1. Unit Tests

### 1.1 `csp-report` view

| Test | Expected |
|---|---|
| Valid payload → 204 + audit row | 1 row with `event='csp_violation'` |
| Invalid JSON → 400 | no audit row |
| Missing `csp-report` key → 400 | no audit row |

```bash
cd backend
pytest apps/security/tests/test_csp_report.py -v
# Expected: 2-3 passed
```

---

## 2. Integration Tests

Not applicable.

## 3. End-to-End Tests

### 3.1 Response headers

```bash
docker compose -f compose.yml -f compose.prod.yml up -d nginx
curl -fsSI http://localhost:80/ | Select-String -Pattern "Content-Security-Policy-Report-Only"
# Expected: 1 match
```

### 3.2 `csp-report` endpoint

```bash
curl -fsS -X POST http://localhost:8000/api/security/csp-report/ -H "Content-Type: application/csp-report" -d '{"csp-report": {"violated-directive": "script-src", "blocked-uri": "https://evil.example/x.js"}}'
echo "Exit code: $LASTEXITCODE"
# Expected: 204
```

### 3.3 Audit row written

```bash
docker compose -f compose.yml -f compose.prod.yml exec api python manage.py shell -c "from apps.audit.models import AuditEvent; print(AuditEvent.objects.filter(event='csp_violation').count())"
# Expected: ≥ 1
```

### 3.4 Playwright spec

```bash
cd frontend
npx playwright test tests/e2e/07_csp.spec.ts --reporter=line
# Expected: 2 passed
```

### 3.5 SPA fallback

```bash
# Serve the built dist/ with a minimal HTTP server that does NOT set CSP
docker run --rm -p 9000:80 -v ${PWD}/frontend/dist:/usr/share/nginx/html:ro nginx:1.27
curl -fsSI http://localhost:9000/ | Select-String -Pattern "Content-Security-Policy"
# Expected: 1 match (the meta tag)
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| `csp-report` view | 3 | passed |
| Report-Only header | 1 | present |
| `csp-report` endpoint | 1 | 204 |
| Audit row | 1 | present |
| Playwright spec | 2 | passed |
| SPA fallback | 1 | present |

---

## 5. Run Tests

### 5.1 Local

```bash
# 1. Boot the stack
docker compose -f compose.yml -f compose.prod.yml up -d

# 2. Unit
cd backend
pytest apps/security/tests/test_csp_report.py -v

# 3. Endpoint
curl -fsS -X POST http://localhost:8000/api/security/csp-report/ -H "Content-Type: application/csp-report" -d '{"csp-report": {"violated-directive": "script-src", "blocked-uri": "https://evil.example/x.js"}}'

# 4. Header
curl -fsSI http://localhost:80/ | Select-String -Pattern "Content-Security-Policy-Report-Only"

# 5. Playwright
cd ../frontend
npx playwright test tests/e2e/07_csp.spec.ts --reporter=line
```

### 5.2 CI

The `e2e` job from QA-03 picks up `tests/e2e/07_csp.spec.ts`. The unit test for the view runs in the `backend` job.

### 5.3 Report-only window

| Day | Action |
|---|---|
| Day 0 | Report-Only deployed |
| Day 1-7 | Collect violation reports; review daily |
| Day 7-14 | If 0 unintended violations, switch to Enforced (follow-up PR) |
| Day 14+ | Enforced permanently |

### 5.4 Failure simulation

To prove the view can reject bad input:

```bash
curl -fsS -X POST http://localhost:8000/api/security/csp-report/ -H "Content-Type: application/csp-report" -d 'not json'
echo "Exit code: $LASTEXITCODE"
# Expected: 400
```

To prove the Playwright spec catches a real injection:

```bash
# Edit 07_csp.spec.ts and remove the assertion
npx playwright test 07_csp.spec.ts
echo "Exit code: $LASTEXITCODE"
# Expected: 1 (failure)
```

Revert the change afterwards.

---

## 6. Cross-links

- [INFRA-01 — Hardened Compose](..) — the nginx service is the policy enforcer.
- [QA-03 — Playwright E2E](..) — share the `auth.ts` helper.
- [QA-05 — OWASP ZAP](..) — ZAP reports CSP violations in the same matrix.
