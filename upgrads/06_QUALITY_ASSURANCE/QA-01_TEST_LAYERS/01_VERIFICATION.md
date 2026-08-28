# QA-01: Verification Commands

> **Instructions:** Run these commands **before** adding tests (Phase 1) to record the baseline, and **after** the implementation (Phase 2) to confirm the new layer count and pass rate.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Count existing tests

```bash
cd backend
pytest --collect-only -q 2>&1 | Select-Object -Last 3
```

**Expected output (before):** A small number such as `7 items collected` (one smoke file).

### Command 1.2 — List the apps' test directories

```bash
Get-ChildItem backend\apps\ -Recurse -Filter "tests" -Directory |
  Select-Object FullName
```

**Expected output (before):** Many apps have no `tests/` directory; only `apps/identity/`, `apps/tenancy/`, `apps/evidence/`, etc. have partial coverage.

### Command 1.3 — Confirm permission / scheduler / migration / failure / smoke tests are missing

```bash
Test-Path backend\apps\tenancy\tests\test_permissions.py
Test-Path backend\apps\tasks\tests\test_scheduler.py
Test-Path backend\tests\test_migrations.py
Test-Path backend\tests\test_failure_injection.py
Test-Path backend\tests\test_release_smoke.py
```

**Expected output (before):** Five `False` lines.

### Command 1.4 — Confirm Playwright is missing in the frontend

```bash
Select-String -Path frontend\package.json -Pattern "@playwright"
```

**Expected output (before):** Zero matches.

---

## Phase 2: Post-Fix Verification

### Command 2.1 — Total test count

```bash
cd backend
pytest --collect-only -q 2>&1 | Select-Object -Last 3
```

**Expected output (after):** `>= 280 items collected`.

### Command 2.2 — Count by layer

```bash
pytest --collect-only -q -m permission | Select-Object -Last 2
pytest --collect-only -q -m scheduler | Select-Object -Last 2
pytest --collect-only -q -m migration | Select-Object -Last 2
pytest --collect-only -q -m failure | Select-Object -Last 2
pytest --collect-only -q -m smoke | Select-Object -Last 2
```

**Expected output (after):** Counts of `>=10`, `>=6`, `>=5`, `>=6`, `>=5` respectively.

### Command 2.3 — Run the new test files in isolation

```bash
cd backend
pytest apps/tenancy/tests/test_permissions.py -v
pytest apps/tasks/tests/test_scheduler.py -v
pytest tests/test_migrations.py -v
pytest tests/test_failure_injection.py -v
pytest tests/test_release_smoke.py -v
```

**Expected output (after):** All files pass, exit code `0`.

### Command 2.4 — Run the full suite

```bash
cd backend
pytest -m "not slow"  # fast feedback
pytest                  # full run
```

**Expected output (after):** `0 failed`, exit code `0`.

### Command 2.5 — Coverage proof (cross-check with QA-02)

```bash
cd backend
pytest --cov=apps --cov-report=term
```

**Expected output (after):** Combined coverage ≥85% per QA-02.

### Command 2.6 — Frontend Playwright presence

```bash
Select-String -Path frontend\package.json -Pattern "@playwright"
```

**Expected output (after):** Match exists (Playwright is added by QA-03).

---

## Phase 3: Regression / Safety

### Command 3.1 — Existing smoke test still green

```bash
cd backend
pytest tests/test_factories_smoke.py -v
```

**Expected output:** `7 passed`.

### Command 3.2 — MyPy and Ruff clean

```bash
cd backend
ruff check apps tests
mypy apps tests
```

**Expected output:** No new violations introduced by the new tests.

### Command 3.3 — Markers registered

```bash
cd backend
pytest --markers 2>&1 | Select-String -Pattern "permission|scheduler|migration|failure|smoke"
```

**Expected output:** At least 5 lines, one per marker.

---

## 4. Final Acceptance

- ✅ Command 1.1 baseline captured
- ✅ Command 1.3 shows 5 missing files; after fix, all 5 files exist
- ✅ Command 2.1 shows `≥280` collected
- ✅ Command 2.3 shows green for each new file
- ✅ Command 2.4 full run is green
- ✅ Command 3.1 smoke remains green
- ✅ Command 3.3 markers registered
