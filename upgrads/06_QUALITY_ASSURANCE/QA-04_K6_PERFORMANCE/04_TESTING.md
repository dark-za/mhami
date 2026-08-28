# QA-04: Test Strategy

> **Rule:** every scenario is a real k6 script that **runs against a real backend**. The thresholds in this file are the same thresholds in the script — no duplication drift.

## 1. Unit Tests

Not applicable — k6 scripts are themselves the test.

## 2. Integration Tests

Not applicable.

## 3. End-to-End (Load) Tests

### 3.1 `api_load.js`

| Stage | VU | Duration |
|---|---|---|
| Ramp-up | 50 | 2m |
| Sustain | 100 | 5m |
| Peak | 200 | 2m |
| Ramp-down | 0 | 2m |

**Thresholds:** `p(95) < 500 ms`, error rate `< 1%`.

**Checks:**
- `login 200`
- `has session` (sessionid cookie present)
- `me 200`

### 3.2 `evidence_load.js`

| Stage | VU | Duration |
|---|---|---|
| Ramp-up | 50 | 2m |
| Sustain | 100 | 5m |
| Peak | 200 | 2m |
| Ramp-down | 0 | 2m |

**Thresholds:** `p(95) < 500 ms`, error rate `< 1%`.

**Checks:**
- `list 200`

### 3.3 `reviews_load.js`

| Stage | VU | Duration |
|---|---|---|
| Ramp-up | 25 | 2m |
| Sustain | 50 | 5m |
| Peak | 100 | 2m |
| Ramp-down | 0 | 2m |

**Thresholds:** `p(95) < 500 ms`, error rate `< 1%`.

**Checks:**
- `decide 200`

### 3.4 `scheduler_load.js`

| Stage | VU | Duration |
|---|---|---|
| Ramp-up | 10 | 1m |
| Sustain | 20 | 3m |
| Peak | 40 | 1m |
| Ramp-down | 0 | 1m |

**Thresholds:** `p(95) < 1000 ms`, error rate `< 1%`.

**Checks:**
- `dispatch 200`

---

## 4. Success Criteria

| Scenario | Stages | Thresholds | Local | CI |
|---|---|---|---|---|
| `api_load` | 4 | p(95) < 500 ms, error < 1% | green | green |
| `evidence_load` | 4 | p(95) < 500 ms, error < 1% | green | green |
| `reviews_load` | 4 | p(95) < 500 ms, error < 1% | green | green |
| `scheduler_load` | 4 | p(95) < 1000 ms, error < 1% | green | green |

---

## 5. Run Tests

### 5.1 Local (smoke)

```bash
docker compose -f compose.prod.yml up -d backend
docker compose -f compose.prod.yml exec backend python manage.py make_load_users
k6 run --duration 30s --vus 5 tests/load/api_load.js
k6 run --duration 30s --vus 5 tests/load/evidence_load.js
k6 run --duration 30s --vus 5 tests/load/reviews_load.js
k6 run --duration 30s --vus 5 tests/load/scheduler_load.js
```

### 5.2 Local (full)

```bash
k6 run tests/load/api_load.js
k6 run tests/load/evidence_load.js
k6 run tests/load/reviews_load.js
k6 run tests/load/scheduler_load.js
```

### 5.3 CI

The `k6` workflow runs nightly at 02:00 UTC. It can also be triggered manually via `workflow_dispatch`.

### 5.4 Inspect

```bash
k6 inspect tests/load/api_load.js
# Expected: printed summary of options, thresholds, scenarios.
```

---

## 6. Failure simulation

To prove the threshold works, temporarily set `p(95)<1` in `api_load.js`:

```js
thresholds: { http_req_duration: ["p(95)<1"] }
```

```bash
k6 run --duration 10s --vus 5 tests/load/api_load.js
echo "Exit code: $LASTEXITCODE"
# Expected: 99 (threshold fail)
```

Restore the threshold afterwards.
