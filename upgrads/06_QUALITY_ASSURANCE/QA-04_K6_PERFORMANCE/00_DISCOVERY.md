# QA-04: Performance Tests (k6)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** There are **no performance tests** in the repository. There is no `tests/load/` directory, no k6 scripts, and no thresholds for `p(95)` latency or error rate. The platform's capacity is unknown; Gate-D cannot be passed without a documented baseline.

**Evidence gathered:**
- `tests/` (root) contains no `load/` subdirectory.
- `.github/workflows/` (if present) has no `k6` job.
- `compose.dev.yml` and `compose.prod.yml` do not include any load-shedding configuration.
- `docs/SERVER_INVENTORY.md` lists target SLOs (latency / throughput), but they are not exercised by any test.

### Impact

| Dimension | Impact |
|---|---|
| Functional | Capacity is unknown; pilot could degrade under realistic load. |
| Operational | No baseline to compare after refactors. |
| Compliance | Gate-D evidence requires performance numbers. |
| Financial | Late discovery of bottlenecks causes re-architecture. |

### Reproducible Evidence

```bash
# 1. Confirm no load tests exist
Get-ChildItem tests -Recurse -Filter "*.js" -ErrorAction SilentlyContinue
# Expected today: 0 files (or no load/ subfolder)

# 2. Confirm no k6 job in CI
Select-String -Path .github\workflows\*.yml -Pattern "k6"
# Expected today: 0 matches

# 3. Confirm no k6 in compose
Select-String -Path compose.yml -Pattern "k6"
# Expected today: 0 matches
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Load test directory | none | `tests/load/*.js` |
| Scenarios | 0 | 4 (login, evidence list, review decision, scheduled job) |
| Threshold `p(95)` | none | < 500 ms |
| Threshold error rate | none | < 1% |
| Stages | none | ramp-up 50 → 100 → 200 → ramp-down |
| CI integration | none | `k6` job that runs nightly |
| Result archiving | none | JSON summary uploaded to S3 / Codecov artifacts |

---

## 3. Goal Statement

> Within **1 week (5 working days)**, install k6, write **4 scenarios** that cover login, evidence listing, review decision, and a scheduled-job dispatch, with a **p(95) < 500 ms** threshold and an **error rate < 1%** threshold — wired into a nightly CI job that publishes a JSON summary.

### Acceptance Criteria

1. **AC-1:** `tests/load/` exists with `api_load.js`, `evidence_load.js`, `reviews_load.js`, and `scheduler_load.js`.
2. **AC-2:** Each scenario uses k6 stages: ramp-up 2m @ 50, sustain 5m @ 100, peak 2m @ 200, ramp-down 2m @ 0.
3. **AC-3:** Each scenario enforces `http_req_duration: ['p(95)<500']` and `http_req_failed: ['rate<0.01']`.
4. **AC-4:** Each scenario is runnable locally with `k6 run tests/load/<name>.js` and exits 0 when thresholds pass.
5. **AC-5:** A `k6` job in `.github/workflows/ci.yml` runs nightly (`cron: '0 2 * * *'`) and uploads `summary.json` as an artifact.
6. **AC-6:** A `tests/load/README.md` documents how to run the suite and how to interpret the summary.
7. **AC-7:** The login scenario uses the **same** `force_login_company` flow as QA-01 (no parallel auth path).

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Backend cannot handle 200 VUs | High | High | Run against a `compose.prod.yml` stack scaled horizontally; document the limit. |
| Flaky results due to shared infra | Medium | High | Reserve a dedicated runner for the nightly job. |
| k6 binary missing in CI | Medium | Medium | Use `grafana/k6` Docker image in the workflow. |
| Test data is exhausted | Medium | High | Seed with factories before each run; reset between scenarios. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `tests/load/` directory | QA Lead | not-started |
| 2 | Write `api_load.js` (login + bootstrap) | QA Lead | not-started |
| 3 | Write `evidence_load.js` (list + detail) | QA Lead | not-started |
| 4 | Write `reviews_load.js` (decision flow) | QA Lead | not-started |
| 5 | Write `scheduler_load.js` (job dispatch) | QA Lead | not-started |
| 6 | Add `k6` job to `.github/workflows/ci.yml` (nightly) | DevOps | not-started |
| 7 | Run locally; record baseline numbers | QA Lead | not-started |
| 8 | Update `docs/SERVER_INVENTORY.md` with thresholds | Tech Writer | not-started |
| 9 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [docs/SERVER_INVENTORY.md](../../../docs/SERVER_INVENTORY.md) — SLOs
- [docs/TEST_STRATEGY.md](../../../docs/TEST_STRATEGY.md) — performance layer
- [compose.prod.yml](../../../compose.prod.yml) — production stack
- [upgrads/06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS](..) — reuse factories
