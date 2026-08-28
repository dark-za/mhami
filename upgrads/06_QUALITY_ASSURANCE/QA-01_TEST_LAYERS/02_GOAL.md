# QA-01: Goal and Plan

## SMART Goal

> Within **2 weeks (10 working days)**, implement the 12 test layers from
> `docs/TEST_STRATEGY.md` and reach a baseline of **≥280 automated tests**
> passing on `pytest`, organised by marker so the fast feedback loop
> (`pytest -m "not slow"`) runs in **under 60 seconds**.

## Detailed Acceptance Standards

### Standard 1: Layer coverage

| Layer | Marker | Minimum Tests | Files |
|---|---|---|---|
| Permission | `permission` | 10 | `apps/tenancy/tests/test_permissions.py` + branch/task/evidence mirrors |
| Scheduler | `scheduler` | 6 | `apps/tasks/tests/test_scheduler.py` |
| Migration | `migration` | 5 | `backend/tests/test_migrations.py` |
| Failure-injection | `failure` | 6 | `backend/tests/test_failure_injection.py` |
| Release smoke | `smoke` | 5 | `backend/tests/test_release_smoke.py` |
| Other (existing) | — | 248+ | existing app tests |
| **Total** | — | **≥280** | — |

### Standard 2: Permission matrix

The permission test must cover at least the matrix:

| Endpoint | Owner | Manager | Supervisor | Employee | Outsider |
|---|---|---|---|---|---|
| `GET /api/v1/tenancy/companies/{id}/` | ✓ | ✗ | ✗ | ✗ | ✗ |
| `GET /api/v1/tasks/instances/` (own branch) | ✓ | ✓ | ✓ | ✓ | ✗ |
| `POST /api/v1/evidence/items/` (own branch) | ✓ | ✓ | ✓ | ✓ | ✗ |
| `GET /api/v1/reviews/decisions/` (all branches) | ✓ | ✓ | ✗ | ✗ | ✗ |
| `POST /api/v1/backups/run/` | ✓ | ✗ | ✗ | ✗ | ✗ |

### Standard 3: Scheduler correctness

`apps/tasks/tests/test_scheduler.py` must use `freezegun` to verify:

1. A job that was due at `2030-01-01 06:00` fires once and only once.
2. A job that becomes due inside the operational cutoff is dispatched within 1 minute.
3. A job whose prerequisite task is still running is skipped (idempotent).
4. A job with a misconfigured cron expression is logged and skipped, not crashed.
5. A job triggered twice in the same second is deduplicated.
6. Disabling a schedule at run-time prevents future fires.

### Standard 4: Migration safety

`backend/tests/test_migrations.py` must use Django's migration executor and assert:

- The migration graph is a **single linear path** (no missing nodes).
- Migrating forward then backward returns to the same schema (column count + table list).
- Tenant, branch, membership, and task rows survive a forward+backward cycle.
- A new column with a default is applied without dropping data.
- A removed field is preserved through the `RenameModel`/`RenameField` migration.

### Standard 5: Failure-injection coverage

`backend/tests/test_failure_injection.py` must cover:

- Redis broker down → Celery job is re-queued, no audit row lost.
- DB connection lost mid-transaction → safe rollback, no partial commit.
- Webhook with bad HMAC → rejected with 401, audit row written.
- Webhook with expired timestamp → rejected, audit row written.
- Oversized media upload (>limit) → rejected with 413, no disk write.
- Missing evidence file → API returns 404, audit row written.

### Standard 6: Release smoke

`backend/tests/test_release_smoke.py` must verify:

- `python manage.py check --deploy` reports no failures.
- `drf-spectacular` can render the schema without error.
- Each app (`tenancy`, `identity`, `tasks`, `evidence`, `reviews`, `exports`, `backups`, `notifications`, `audit`, `ai_gateway`, `connector_control`) exposes a healthy `health/` or root URL.
- The `force_login_company` factory boots a client and reaches `/api/v1/tenancy/companies/me/`.
- `make_migrate` round-trip is idempotent.

---

## Detailed Implementation Plan

### Week 1 — Permission + Scheduler (Days 1-5)

**Day 1**
- [ ] Add `pytest.mark.*` markers in `pyproject.toml`.
- [ ] Inventory the existing endpoints and the role/branch matrix.

**Day 2-3**
- [ ] Write `apps/tenancy/tests/test_permissions.py` (10 tests).
- [ ] Mirror to `apps/tasks/tests/test_permissions.py`, `apps/evidence/tests/test_permissions.py`, `apps/reviews/tests/test_permissions.py`, `apps/backups/tests/test_permissions.py`.

**Day 4-5**
- [ ] Write `apps/tasks/tests/test_scheduler.py` (6 tests) with `freezegun`.
- [ ] Run `pytest -m scheduler -v` and confirm green.

### Week 2 — Migration + Failure + Smoke (Days 6-10)

**Day 6-7**
- [ ] Write `backend/tests/test_migrations.py` (5 tests).
- [ ] Run in CI under `compose.dev.yml`.

**Day 8-9**
- [ ] Write `backend/tests/test_failure_injection.py` (6 tests).
- [ ] Mock Redis with `fakeredis`, mock HMAC with a bad signature fixture.

**Day 10**
- [ ] Write `backend/tests/test_release_smoke.py` (5 tests).
- [ ] Run the full suite: `pytest -m "not slow"` (fast) and `pytest` (full).
- [ ] Update `docs/TEST_STRATEGY.md` and `CHANGELOG.md`.

---

## Dependency Graph

```
Markers in pyproject.toml
    ↓
Permission tests (4 files)
    ↓
Scheduler tests
    ↓
Migration tests
    ↓
Failure-injection tests
    ↓
Release smoke tests
    ↓
pytest --collect-only  (≥280)
    ↓
pytest                  (exit 0)
    ↓
Update docs + CHANGELOG
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Markers registered; permission matrix agreed | QA Lead |
| CP-2 | Permission tests pass | Backend |
| CP-3 | Scheduler tests pass (frozen time) | Backend |
| CP-4 | Migration tests pass | Backend |
| CP-5 | Failure-injection tests pass | Backend |
| CP-6 | Release smoke passes | Backend |
| CP-7 | ≥280 collected, full run green | QA Lead |
| CP-8 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If the layer count cannot reach 280 within 2 weeks.
- If any new test introduces a flaky pattern (network, time, randomness) without a deterministic fix.
- If the permission matrix contradicts `SECURITY_THREAT_MODEL.md` — escalate to security review first.
