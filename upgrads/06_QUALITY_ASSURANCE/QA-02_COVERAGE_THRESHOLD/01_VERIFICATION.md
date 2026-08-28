# QA-02: Verification Commands

> **Instructions:** Run the baseline (Phase 1) before the change, then the post-fix (Phase 2) to confirm the floor and CI integration.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Confirm no coverage tool config in backend

```bash
Select-String -Path backend\pyproject.toml -Pattern "tool.coverage"
```

**Expected output (before):** 0 matches.

### Command 1.2 — Confirm no thresholds in frontend

```bash
Select-String -Path frontend\vite.config.ts -Pattern "thresholds"
```

**Expected output (before):** 0 matches.

### Command 1.3 — Capture baseline coverage

```bash
cd backend
pytest --cov=apps --cov-report=term 2>&1 | Select-Object -Last 20
```

**Expected output (before):** Unknown % (often < 30% with the current test count).

### Command 1.4 — Try to fail the build on threshold

```bash
cd backend
pytest --cov=apps --cov-fail-under=85 2>&1 | Select-Object -Last 10
echo "Exit code: $LASTEXITCODE"
```

**Expected output (before):** Exit code `0` (no threshold is enforced).

### Command 1.5 — Confirm Codecov upload missing in CI

```bash
Get-ChildItem .github\workflows -Recurse -ErrorAction SilentlyContinue
Select-String -Path .github\workflows\*.yml -Pattern "codecov"
```

**Expected output (before):** 0 matches.

---

## Phase 2: Post-Fix Verification

### Command 2.1 — Coverage tool config exists

```bash
Select-String -Path backend\pyproject.toml -Pattern "tool.coverage"
Select-String -Path backend\pyproject.toml -Pattern "fail_under = 85"
```

**Expected output (after):** Matches in both lines.

### Command 2.2 — Run with the floor

```bash
cd backend
pytest --cov=apps --cov-fail-under=85
```

**Expected output (after):** Exit code `0`, summary line `TOTAL ... ≥ 85%`.

### Command 2.3 — XML + HTML produced

```bash
cd backend
pytest --cov=apps --cov-report=xml --cov-report=html
Test-Path coverage.xml
Test-Path htmlcov\index.html
```

**Expected output (after):** Both `True`.

### Command 2.4 — Frontend thresholds exist

```bash
Select-String -Path frontend\vite.config.ts -Pattern "lines: 70"
Select-String -Path frontend\vite.config.ts -Pattern "branches: 65"
```

**Expected output (after):** Both present.

### Command 2.5 — Frontend coverage run

```bash
cd frontend
npm run test -- --coverage
```

**Expected output (after):** Thresholds enforced; non-zero exit if below the floor.

### Command 2.6 — Codecov badge in README

```bash
Select-String -Path README.md -Pattern "codecov"
```

**Expected output (after):** Match present.

### Command 2.7 — CI runs the coverage step

```bash
Get-ChildItem .github\workflows -ErrorAction SilentlyContinue
Select-String -Path .github\workflows\*.yml -Pattern "codecov"
```

**Expected output (after):** Match present.

---

## Phase 3: Regression / Safety

### Command 3.1 — Existing tests still green

```bash
cd backend
pytest
```

**Expected output (after):** All tests green; coverage ≥ 85%.

### Command 3.2 — Coverage delta visible

```bash
cd backend
coverage report --skip-covered --sort=cover
```

**Expected output (after):** Sorted list shows lowest-covered files (drives future test work).

### Command 3.3 — Coverage for migrations and tests is excluded

```bash
coverage report --include="apps/*" --omit="*/migrations/*,*/tests/*,*/admin.py"
```

**Expected output (after):** Number matches the threshold.

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.4 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 green
- ✅ Command 2.5 frontend thresholds enforced
- ✅ Command 2.6 / 2.7 badge + CI upload in place
- ✅ Command 3.1 full suite green
- ✅ Command 3.2 lowest-covered files documented
