# QA-03: Verification Commands

> **Instructions:** Run baseline (Phase 1) before the change, then post-fix (Phase 2) to confirm the runner and tests are wired in.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Confirm Playwright missing

```bash
Select-String -Path frontend\package.json -Pattern "@playwright"
```

**Expected output (before):** 0 matches.

### Command 1.2 — Confirm no `playwright.config.ts`

```bash
Test-Path frontend\playwright.config.ts
```

**Expected output (before):** `False`.

### Command 1.3 — Confirm no `tests/e2e/`

```bash
Test-Path frontend\tests\e2e
```

**Expected output (before):** `False`.

### Command 1.4 — Confirm no E2E job in CI

```bash
Get-ChildItem .github\workflows -ErrorAction SilentlyContinue
Select-String -Path .github\workflows\*.yml -Pattern "playwright"
```

**Expected output (before):** 0 matches.

---

## Phase 2: Post-Fix Verification

### Command 2.1 — Playwright installed

```bash
Select-String -Path frontend\package.json -Pattern "@playwright"
# Expected: 1 match
```

### Command 2.2 — Config exists

```bash
Test-Path frontend\playwright.config.ts
# Expected: True
```

### Command 2.3 — Spec files present

```bash
Get-ChildItem frontend\tests\e2e -Recurse -Filter "*.spec.ts" | Measure-Object | Select-Object -ExpandProperty Count
# Expected: 5
```

### Command 2.4 — Total tests ≥ 30

```bash
cd frontend
npx playwright test --list 2>&1 | Select-Object -Last 3
# Expected: >= 30 specs collected
```

### Command 2.5 — Run locally (with a real backend)

```bash
cd compose
docker compose -f compose.dev.yml up -d backend
cd ../frontend
npx playwright test --reporter=line
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### Command 2.6 — Trace + video on

```bash
Test-Path frontend\test-results
Get-ChildItem frontend\test-results -ErrorAction SilentlyContinue | Select-Object -First 5
# Expected: at least trace.zip or video.webm files
```

### Command 2.7 — CI job added

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "playwright"
# Expected: 1+ match
```

### Command 2.8 — Browser binaries cached in CI

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "playwright install"
# Expected: 1 match
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Unit tests still green

```bash
cd frontend
npm run test
# Expected: green
```

### Command 3.2 — Typecheck still green

```bash
cd frontend
npm run typecheck
# Expected: exit 0
```

### Command 3.3 — Build still green

```bash
cd frontend
npm run build
# Expected: dist/ produced
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 green
- ✅ Command 2.7 / 2.8 CI wired in
- ✅ Command 3.1 / 3.2 / 3.3 no regression
