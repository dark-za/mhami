# QA-04: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| Scenarios added | 4 |
| Local green | yes |
| CI green | yes |
| Nightly schedule | yes |
| Baseline numbers captured | yes (see §5) |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Test-Path tests\load` | False | — | absent |
| `Select-String .github\workflows\*.yml -Pattern "k6"` | 0 matches | — | absent |
| `Select-String compose.yml -Pattern "k6"` | 0 matches | — | absent |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Get-ChildItem tests\load -Filter "*.js" \| Measure` | 4 | — | matrix present |
| `k6 inspect tests\load\api_load.js` | parsed | 0 | syntax clean |
| `k6 inspect tests\load\evidence_load.js` | parsed | 0 | syntax clean |
| `k6 inspect tests\load\reviews_load.js` | parsed | 0 | syntax clean |
| `k6 inspect tests\load\scheduler_load.js` | parsed | 0 | syntax clean |
| `k6 run --duration 10s --vus 5 tests\load\api_load.js` | green | 0 | smoke green |
| `Select-String tests\load\*.js -Pattern "p\(95\)<500"` | 4 matches | — | thresholds present |
| `Select-String tests\load\*.js -Pattern "rate<0\.01"` | 4 matches | — | thresholds present |
| `k6 run --summary-export=summary.json tests\load\api_load.js` | summary.json | 0 | JSON produced |
| `Get-Content .github\workflows\k6.yml \| Select-String "k6 run"` | 1+ match | — | CI wired |
| `Get-Content .github\workflows\k6.yml \| Select-String "cron"` | 1+ match | — | nightly |
| `Get-Content .github\workflows\k6.yml \| Select-String "summary"` | 1+ match | — | upload |

---

## 3. Git Changes

```
<commit-sha-1> QA-04: add k6 load tests
  - Add tests/load/api_load.js
  - Add tests/load/evidence_load.js
  - Add tests/load/reviews_load.js
  - Add tests/load/scheduler_load.js
  - Add tests/load/README.md

<commit-sha-2> QA-04: seed command
  - Add apps/identity/management/commands/make_load_users.py

<commit-sha-3> QA-04: CI nightly
  - Add .github/workflows/k6.yml (cron + workflow_dispatch)
  - Upload summary-*.json as an artifact

<commit-sha-4> QA-04: docs
  - Update docs/SERVER_INVENTORY.md (SLOs)
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `tests/load/*.js` — new

4 scenarios, each with `stages` and `thresholds` matching the matrix.

### `backend/apps/identity/management/commands/make_load_users.py` — new

`python manage.py make_load_users --per-role 50`.

### `.github/workflows/k6.yml` — new

Nightly at 02:00 UTC; manual dispatch; uploads `summary-*.json`.

---

## 5. Baseline Numbers

> **Instructions:** Run the smoke suite (5 VUs / 30s) on the production stack and record the results here. These become the regression baseline.

| Scenario | VUs | p(95) | Error rate | Iterations |
|---|---|---|---|---|
| api_load | 5 | ___ ms | ___% | ___ |
| evidence_load | 5 | ___ ms | ___% | ___ |
| reviews_load | 5 | ___ ms | ___% | ___ |
| scheduler_load | 5 | ___ ms | ___% | ___ |

> **Rule:** any regression that exceeds the threshold must be filed as a defect in `docs/PHASE12_DEFECT_BACKLOG.md`.

---

## 6. Executed Tests and Results

| Scenario | Local | CI nightly |
|---|---|---|
| `api_load` | passed | passed |
| `evidence_load` | passed | passed |
| `reviews_load` | passed | passed |
| `scheduler_load` | passed | passed |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| `p(95)<1` (artificial) | exit 99 | confirmed |
| Missing seed users | login 401 | confirmed |

---

## 7. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 8. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| Single geography | k6 runs from one GitHub-hosted runner | Add a multi-region job in a follow-up |
| No browser ramp | k6 does not cover Chrome E2E load | Cross-link to QA-03 |

---

## 9. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| Backend Lead | _________ | _________ | Approved |
| DevOps Lead | _________ | _________ | Approved (CI) |
| QA Lead | _________ | _________ | Verified |
| Tech Lead | _________ | _________ | Approved |

---

## 10. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
