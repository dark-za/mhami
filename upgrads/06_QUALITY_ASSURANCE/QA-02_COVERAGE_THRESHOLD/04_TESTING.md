# QA-02: Test Strategy

> **Rule:** coverage is a **floor**, not a target. The goal of these tests is to **fail the build** when the floor is not met. The test count is therefore 1: a single `pytest` invocation that returns exit code 0 with the `--cov-fail-under=85` flag.

## 1. Unit Tests

Not applicable — QA-02 is a configuration change, not a feature.

## 2. Integration Tests

Not applicable.

## 3. End-to-End Tests

### 3.1 Backend coverage floor

```bash
cd backend
pytest --cov=apps --cov-fail-under=85
```

**Expected:** Exit code `0`. The summary line `TOTAL ... ≥ 85%`.

### 3.2 Backend coverage artefacts

```bash
cd backend
pytest --cov=apps --cov-report=xml --cov-report=html
Test-Path coverage.xml
Test-Path htmlcov\index.html
```

**Expected:** Both `True`.

### 3.3 Frontend coverage floor

```bash
cd frontend
npm run coverage
```

**Expected:** Exit code `0`. Vitest output shows `lines ≥ 70`, `functions ≥ 70`, `branches ≥ 65`, `statements ≥ 70`.

### 3.4 Frontend lcov

```bash
Test-Path frontend\coverage\lcov.info
```

**Expected:** `True`.

### 3.5 CI integration

```bash
Get-Content .github/workflows/ci.yml | Select-String -Pattern "cov-fail-under"
Get-Content .github/workflows/ci.yml | Select-String -Pattern "codecov"
```

**Expected:** At least 2 matches (1 in backend job, 1 in upload step).

### 3.6 Badge

```bash
Select-String -Path README.md -Pattern "codecov"
```

**Expected:** 1+ match.

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| Backend `pytest --cov-fail-under=85` | 1 | passed |
| Backend `coverage.xml` produced | 1 | present |
| Backend `htmlcov/index.html` produced | 1 | present |
| Frontend `npm run coverage` | 1 | passed |
| Frontend `lcov.info` produced | 1 | present |
| CI has coverage step | 1 | present |
| Codecov upload step | 1 | present |
| Badge in README | 1 | present |
| Secret documented | 1 | present |

---

## 5. Run Tests

### 5.1 Local

```bash
# Backend
cd backend
pytest --cov=apps --cov-fail-under=85

# Frontend
cd frontend
npm run coverage
```

### 5.2 CI

Push to a branch; the `ci.yml` workflow runs the coverage step and uploads to Codecov. The badge in `README.md` updates automatically.

### 5.3 Failure simulation

To prove the floor works, temporarily set `fail_under = 99` in `pyproject.toml` and run:

```bash
cd backend
pytest --cov=apps --cov-fail-under=99
echo "Exit code: $LASTEXITCODE"
# Expected: 2 (fail-under)
```

Restore `fail_under = 85` afterwards.

---

## 6. Cross-links

- [QA-01 — Test Layers](..) — must land first; QA-02's floor assumes ≥280 tests.
- [docs/TEST_STRATEGY.md](../../../docs/TEST_STRATEGY.md) — coverage is listed as a release gate.
- [docs/SECRET_MANAGEMENT.md](../../../docs/SECRET_MANAGEMENT.md) — `CODECOV_TOKEN` is registered.
