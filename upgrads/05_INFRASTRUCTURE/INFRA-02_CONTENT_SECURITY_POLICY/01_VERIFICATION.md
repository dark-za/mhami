# INFRA-02: Verification Commands

> **Instructions:** Run baseline (Phase 1) before the change, then post-fix (Phase 2) to confirm CSP is deployed in `Report-Only`, the SPA fallback is in place, and the Playwright test passes.

## Phase 1: Pre-Fix Proof

### Command 1.1 — CSP missing from nginx

```bash
Select-String -Path infra\nginx\security-headers.conf -Pattern "Content-Security-Policy"
# Expected: 0 matches
```

### Command 1.2 — CSP missing from SPA

```bash
Select-String -Path frontend\index.html -Pattern "Content-Security-Policy"
# Expected: 0 matches
```

### Command 1.3 — Vite does not inject a nonce

```bash
Select-String -Path frontend\vite.config.ts -Pattern "nonce"
# Expected: 0 matches
```

### Command 1.4 — Response headers do not include CSP

```bash
docker compose -f compose.yml up -d api frontend
curl -fsSI http://localhost:3000/ | Select-String -Pattern "Content-Security-Policy"
# Expected: 0 matches
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — `Report-Only` in nginx

```bash
Select-String -Path infra\nginx\security-headers.conf -Pattern "Content-Security-Policy-Report-Only"
# Expected: 1 match
```

### Command 2.2 — `report-uri` directive

```bash
Select-String -Path infra\nginx\security-headers.conf -Pattern "report-uri"
# Expected: 1 match, value = /api/security/csp-report/
```

### Command 2.3 — SPA fallback meta tag

```bash
Select-String -Path frontend\index.html -Pattern "Content-Security-Policy"
# Expected: 1 match
```

### Command 2.4 — Response headers

```bash
docker compose -f compose.yml -f compose.prod.yml up -d nginx
curl -fsSI http://localhost:80/ | Select-String -Pattern "Content-Security-Policy-Report-Only"
# Expected: 1 match
```

### Command 2.5 — `csp-report` view

```bash
curl -fsS -X POST http://localhost:8000/api/security/csp-report/ -H "Content-Type: application/csp-report" -d '{"csp-report": {"violated-directive": "script-src", "blocked-uri": "https://evil.example/x.js"}}'
echo "Exit code: $LASTEXITCODE"
# Expected: 204 No Content
```

### Command 2.6 — Audit row written

```bash
docker compose -f compose.yml -f compose.prod.yml exec api python manage.py shell -c "from apps.audit.models import AuditEvent; print(AuditEvent.objects.filter(event='csp_violation').count())"
# Expected: >= 1
```

### Command 2.7 — Playwright spec passes

```bash
cd frontend
npx playwright test tests/e2e/07_csp.spec.ts --reporter=line
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### Command 2.8 — Threat model updated

```bash
Select-String -Path docs\SECURITY_THREAT_MODEL.md -Pattern "Content-Security-Policy"
# Expected: 1+ match
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Existing E2E still green

```bash
cd frontend
npx playwright test --reporter=line
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### Command 3.2 — Existing unit tests still green

```bash
cd frontend
npm run test
# Expected: green
```

### Command 3.3 — nginx config valid

```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx nginx -t
# Expected: "syntax is ok" / "test is successful"
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 / 1.4 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 / 2.6 / 2.7 / 2.8 green
- ✅ Command 3.1 / 3.2 / 3.3 no regression
