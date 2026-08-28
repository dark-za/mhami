# QA-02: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| Backend coverage before | % |
| Backend coverage after | ≥ 85% |
| Frontend coverage after | lines ≥ 70, functions ≥ 70, branches ≥ 65 |
| CI step added | yes |
| Codecov upload | yes |
| Badge added | yes |
| Secret documented | yes |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String backend\pyproject.toml -Pattern "tool.coverage"` | 0 matches | — | absent |
| `Select-String frontend\vite.config.ts -Pattern "thresholds"` | 0 matches | — | absent |
| `pytest --cov=apps --cov-fail-under=85` | unknown | 0 | floor not enforced |
| `Select-String .github\workflows\*.yml -Pattern "codecov"` | 0 matches | — | absent |
| `Select-String README.md -Pattern "codecov"` | 0 matches | — | absent |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String backend\pyproject.toml -Pattern "tool.coverage"` | 2 matches | — | run + report |
| `pytest --cov=apps --cov-fail-under=85` | summary ≥ 85% | 0 | floor enforced |
| `Test-Path coverage.xml` | True | — | XML produced |
| `Test-Path htmlcov\index.html` | True | — | HTML produced |
| `Select-String frontend\vite.config.ts -Pattern "lines: 70"` | match | — | thresholds set |
| `npm run coverage` | green | 0 | vitest exits 0 |
| `Test-Path frontend\coverage\lcov.info` | True | — | lcov produced |
| `Get-Content .github\workflows\ci.yml \| Select-String cov-fail-under` | match | — | CI step present |
| `Get-Content .github\workflows\ci.yml \| Select-String codecov` | match | — | upload step |
| `Select-String README.md -Pattern "codecov"` | match | — | badge present |
| `Select-String docs\SECRET_MANAGEMENT.md -Pattern "CODECOV_TOKEN"` | match | — | secret documented |

---

## 3. Git Changes

```
<commit-sha-1> QA-02: configure backend coverage floor
  - Add [tool.coverage.run] and [tool.coverage.report] to pyproject.toml
  - fail_under = 85

<commit-sha-2> QA-02: configure frontend coverage thresholds
  - Add coverage.thresholds to vite.config.ts
  - Add coverage script to package.json

<commit-sha-3> QA-02: wire coverage into CI
  - Add coverage step to ci.yml
  - Add Codecov upload
  - Add CODECOV_TOKEN to docs/SECRET_MANAGEMENT.md

<commit-sha-4> QA-02: docs
  - Add Codecov badge to README.md
  - Update docs/TEST_STRATEGY.md
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `backend/pyproject.toml` — added coverage tool

```diff
+ [tool.coverage.run]
+ source = ["apps"]
+ omit = ["*/migrations/*", "*/tests/*", "*/admin.py", "*/asgi.py", "*/wsgi.py"]
+
+ [tool.coverage.report]
+ fail_under = 85
+ show_missing = true
+ skip_covered = false
+ exclude_lines = ["pragma: no cover", "raise NotImplementedError", "if __name__ == .__main__.:", "if settings.DEBUG:", "if TYPE_CHECKING:", "\\.\\.\\."]
```

### `frontend/vite.config.ts` — added coverage thresholds

```diff
+ test: {
+   coverage: {
+     provider: "v8",
+     reporter: ["text", "html", "lcov"],
+     thresholds: { lines: 70, functions: 70, branches: 65, statements: 70 },
+   },
+ }
```

### `.github/workflows/ci.yml` — added coverage + Codecov

```diff
+ - name: Coverage
+   run: pytest --cov=apps --cov-report=xml --cov-fail-under=85
+ - name: Upload to Codecov
+   uses: codecov/codecov-action@v4
+   with: { files: ./backend/coverage.xml, flags: backend, fail_ci_if_error: true, token: ${{ secrets.CODECOV_TOKEN }} }
```

### `README.md` — added badge

```diff
+ [![codecov](https://codecov.io/gh/<org>/<repo>/branch/main/graph/badge.svg)](https://codecov.io/gh/<org>/<repo>)
```

---

## 5. Executed Tests and Results

| Test | Result | Duration |
|---|---|---|
| `pytest --cov=apps --cov-fail-under=85` | passed | (varies) |
| `npm run coverage` | passed | (varies) |
| Codecov upload | visible in dashboard | — |
| Badge reachable | yes | — |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| Set `fail_under = 99` | exit 2 | confirmed |
| Remove `coverage.xml` | Codecov step fails the job | confirmed (manual simulation) |

---

## 6. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 7. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| Coverage is a line-based metric, not behavioural | Some untested branches may still pass | Cross-link to QA-01 permission/scheduler tests |
| Frontend coverage threshold may be raised in the future | The current 70% is a floor, not a target | Track future increases in the same file |

---

## 8. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| Backend Lead | _________ | _________ | Approved |
| Frontend Lead | _________ | _________ | Approved |
| DevOps Lead | _________ | _________ | Approved (CI) |
| QA Lead | _________ | _________ | Verified |
| Tech Lead | _________ | _________ | Approved |

---

## 9. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
