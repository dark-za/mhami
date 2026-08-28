# QA-04: Goal and Plan

## SMART Goal

> Within **1 week (5 working days)**, install k6, write **4 load scenarios**
> (login, evidence list, review decision, scheduled job), enforce
> **`p(95) < 500 ms`** and **`error rate < 1%`**, run them against a
> `compose.prod.yml` stack, and wire a **nightly CI job** that publishes
> a JSON summary.

## Detailed Acceptance Standards

### Standard 1: Scenario matrix

| File | Endpoint | VU stages | Threshold |
|---|---|---|---|
| `api_load.js` | `POST /api/v1/auth/login` + `GET /api/v1/tenancy/companies/me/` | 50 → 100 → 200 → 0 | p(95) < 500 ms, error < 1% |
| `evidence_load.js` | `GET /api/v1/evidence/items/` (paginated) | 50 → 100 → 200 → 0 | p(95) < 500 ms, error < 1% |
| `reviews_load.js` | `POST /api/v1/reviews/decisions/{id}/decide/` | 25 → 50 → 100 → 0 | p(95) < 500 ms, error < 1% |
| `scheduler_load.js` | simulated scheduler tick → `dispatch_due_jobs` | 10 → 20 → 40 → 0 | p(95) < 1000 ms, error < 1% |

### Standard 2: Stages

```js
export const options = {
  stages: [
    { duration: "2m", target: 50 },
    { duration: "5m", target: 100 },
    { duration: "2m", target: 200 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};
```

### Standard 3: Auth reuse

Each scenario obtains a session through `POST /api/v1/auth/login` and reuses the cookie via `http.cookieJar`. No parallel auth path is allowed.

### Standard 4: CI integration

`.github/workflows/ci.yml` must have a `k6` job that:

```yaml
on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:
```

The job uses `grafana/k6:latest` as the container image, mounts the repository, runs each scenario with `--summary-export`, and uploads the JSON files as artifacts.

### Standard 5: Documentation

`tests/load/README.md` documents:

- How to run locally.
- How to interpret `summary.json`.
- The SLO table (p(95) < 500 ms, error < 1%).
- How to seed data with the QA-01 factories.

### Standard 6: Cross-link with QA-01

The login scenario reuses the same credential set as the QA-01 permission tests, so a backend change that breaks login is detected in both layers.

---

## Detailed Implementation Plan

### Day 1 — Setup

**Morning**
- [ ] Add `tests/load/` directory.
- [ ] Install k6 locally.
- [ ] Document the install path in `tests/load/README.md`.

**Afternoon**
- [ ] Decide on the seeded user pool (4 roles × 50 users each).
- [ ] Add a `make-load-users` management command (cross-link to QA-01 factories).

### Day 2-3 — Scenarios

**Day 2**
- [ ] Write `api_load.js` (login + bootstrap).
- [ ] Write `evidence_load.js` (list + detail).

**Day 3**
- [ ] Write `reviews_load.js` (decision flow).
- [ ] Write `scheduler_load.js` (job dispatch).

### Day 4 — Local run

- [ ] Boot `compose.prod.yml` locally.
- [ ] Run each scenario with 5 VUs for 30s as a smoke test.
- [ ] Capture baseline numbers in `tests/load/baseline.md`.

### Day 5 — CI

- [ ] Add `k6` job to `.github/workflows/ci.yml` (nightly + manual).
- [ ] Open a PR; verify the artifact upload.
- [ ] Update `docs/SERVER_INVENTORY.md` and `CHANGELOG.md`.

---

## Dependency Graph

```
k6 binary / Docker image
    ↓
tests/load/*.js (4 scenarios)
    ↓
local run + baseline
    ↓
CI nightly job
    ↓
artifact upload
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | k6 installable; seed command merged | QA Lead |
| CP-2 | All 4 scenarios syntactically valid | QA Lead |
| CP-3 | Local smoke green | QA Lead |
| CP-4 | CI nightly job green | DevOps |
| CP-5 | Artifacts archived | DevOps |
| CP-6 | Docs updated | Tech Writer |

---

## Cancellation Criteria

- If the backend cannot handle 50 VUs at `p(95) < 500 ms` → escalate infra; do not relax the threshold.
- If k6 is not available in the target environment → fall back to Locust; the thresholds stay the same.
