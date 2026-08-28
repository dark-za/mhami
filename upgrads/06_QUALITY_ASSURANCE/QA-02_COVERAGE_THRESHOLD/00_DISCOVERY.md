# QA-02: Mandatory Coverage Threshold (≥85%)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** There is no enforced coverage threshold. The repository has `pytest-cov` available in `pyproject.toml` but no `[tool.coverage]` configuration, no `--cov-fail-under`, and no Codecov integration. Coverage is not visible in CI.

**Evidence gathered:**
- `backend/pyproject.toml` lists `pytest-cov==6.0.0` as a dependency but defines no coverage tool settings.
- `backend/conftest.py` uses `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")` — no coverage hook.
- `frontend/package.json` uses Vitest with `coverage.reporter: ['text']` only in the standard Vitest config; thresholds are not enforced.
- CI workflow files in `.github/workflows/` (if any) are not configured to fail on coverage regression.

### Impact

| Dimension | Impact |
|---|---|
| Functional | Untested code can ship; coverage blind spots hide real defects. |
| Security | A coverage floor would force permission/scheduler tests to be added (cross-link to QA-01). |
| Operational | No objective measure of test quality. |
| Compliance | Cannot evidence test depth for Gate-D. |
| Financial | Late defect discovery is more expensive. |

### Reproducible Evidence

```bash
# 1. Confirm no coverage config exists
Select-String -Path backend\pyproject.toml -Pattern "tool.coverage"
# Expected today: 0 matches

# 2. Confirm pytest-cov is available but not configured
Select-String -Path backend\pyproject.toml -Pattern "pytest-cov"
# Expected today: 1 match (the dependency)

# 3. Try running with coverage to see the baseline
cd backend
pytest --cov=apps --cov-report=term 2>&1 | Select-Object -Last 15
# Expected today: unknown %, no fail-under, no threshold

# 4. Frontend coverage thresholds
Select-String -Path frontend\vite.config.ts -Pattern "thresholds"
# Expected today: 0 matches
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Backend coverage config | none | `[tool.coverage.run]` + `[tool.coverage.report]` with `fail_under=85` |
| Backend coverage in CI | none | `pytest --cov=apps --cov-fail-under=85` and Codecov upload |
| Frontend coverage thresholds | none | lines/functions ≥70, branches ≥65 |
| Coverage visibility | local only | Codecov badge in `README.md` |
| Coverage report artifacts | none | `coverage.xml` + `lcov.info` |
| Coverage guard for migrations | none | `pytest --cov=apps --cov-fail-under=85` in `migrations.yml` |

---

## 3. Goal Statement

> Within **3 working days**, configure **backend and frontend coverage** with an enforced floor of **85% (backend)** and **70%/70%/65% (frontend)**, fail the CI on regression, upload the reports to Codecov, and add the badge to `README.md`.

### Acceptance Criteria

1. **AC-1:** `[tool.coverage.run]` and `[tool.coverage.report]` exist in `backend/pyproject.toml`, with `source = ["apps"]`, omit migrations/tests/admin, and `fail_under = 85`.
2. **AC-2:** `pytest --cov=apps --cov-fail-under=85` exits 0 on a clean run.
3. **AC-3:** `pytest --cov=apps` produces both `coverage.xml` and an HTML report under `backend/htmlcov/`.
4. **AC-4:** A CI job runs the coverage command, uploads `coverage.xml` to Codecov, and fails the build if `fail_under` is not met.
5. **AC-5:** Frontend `vite.config.ts` configures `coverage.thresholds = { lines: 70, functions: 70, branches: 65 }`.
6. **AC-6:** `npm run test -- --coverage` produces `lcov.info` and exits non-zero when the thresholds are not met.
7. **AC-7:** `README.md` shows a Codecov badge.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Coverage drop after the change | High | High | Add `coverage.py` only after QA-01 has landed the missing tests. |
| False sense of safety | Medium | High | Combine coverage with permission/scheduler smoke (cross-link to QA-01). |
| Codecov token missing in CI | Medium | Medium | Document the `CODECOV_TOKEN` secret in `docs/SECRET_MANAGEMENT.md`. |
| Frontend coverage low | Medium | Medium | Start with a baseline run; raise the threshold iteratively. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `[tool.coverage.run]` + `[tool.coverage.report]` to `pyproject.toml` | Backend | not-started |
| 2 | Run `pytest --cov=apps` and capture baseline | QA Lead | not-started |
| 3 | Add `coverage` step to CI with `--cov-fail-under=85` | DevOps | not-started |
| 4 | Add Codecov upload to CI | DevOps | not-started |
| 5 | Configure Vitest `coverage.thresholds` in `vite.config.ts` | Frontend | not-started |
| 6 | Add `npm run coverage` script and run locally | Frontend | not-started |
| 7 | Add Codecov badge to `README.md` | Tech Writer | not-started |
| 8 | Update `docs/TEST_STRATEGY.md` and `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [backend/pyproject.toml](../../../backend/pyproject.toml)
- [frontend/vite.config.ts](../../../frontend/vite.config.ts)
- [docs/SECRET_MANAGEMENT.md](../../../docs/SECRET_MANAGEMENT.md)
- [docs/TEST_STRATEGY.md](../../../docs/TEST_STRATEGY.md)
- [QA-01 — Test Layers](..) (must land first)
