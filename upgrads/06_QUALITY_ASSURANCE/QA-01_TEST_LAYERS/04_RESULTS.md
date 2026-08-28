# QA-01: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| Number of Modified Files | N |
| Number of Added Lines | N |
| Number of Removed Lines | N |
| Total tests added | ≥215 |
| Total tests now collected | ≥280 |
| Layer markers registered | 5 (permission, scheduler, migration, failure, smoke) |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `pytest --collect-only -q \| Select -Last 3` | `~7 items` | 0 | only smoke |
| `Test-Path backend\apps\tenancy\tests\test_permissions.py` | `False` | — | missing |
| `Test-Path backend\apps\tasks\tests\test_scheduler.py` | `False` | — | missing |
| `Test-Path backend\tests\test_migrations.py` | `False` | — | missing |
| `Test-Path backend\tests\test_failure_injection.py` | `False` | — | missing |
| `Test-Path backend\tests\test_release_smoke.py` | `False` | — | missing |
| `pytest --markers \| Select-String` | empty | — | no markers |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `pytest --collect-only -q \| Select -Last 3` | `≥280 items` | 0 | target met |
| `pytest -m permission` | ≥10 passed | 0 | matrix green |
| `pytest -m scheduler` | ≥6 passed | 0 | freezegun green |
| `pytest -m migration` | ≥5 passed | 0 | round-trip green |
| `pytest -m failure` | ≥6 passed | 0 | harness green |
| `pytest -m smoke` | ≥5 passed | 0 | boots green |
| `pytest -m "not slow"` | all green | 0 | fast feedback |
| `pytest` | all green | 0 | full run |
| `pytest --cov=apps --cov-fail-under=85` | ≥85% | 0 | cross-check QA-02 |
| `ruff check apps tests` | clean | 0 | no new violations |
| `mypy apps tests` | clean | 0 | no new violations |

---

## 3. Git Changes

```
<commit-sha-1> QA-01: register pytest markers
  - Update pyproject.toml with [tool.pytest.ini_options]
  - Add permission, scheduler, migration, failure, smoke markers

<commit-sha-2> QA-01: add permission tests across apps
  - Create apps/tenancy/tests/test_permissions.py (10 tests)
  - Mirror to apps/{tasks,evidence,reviews,backups}/tests/test_permissions.py

<commit-sha-3> QA-01: add scheduler tests with freezegun
  - Create apps/tasks/tests/test_scheduler.py (6 tests)
  - Add make_task_schedule and make_task_instance factories

<commit-sha-4> QA-01: add migration round-trip tests
  - Create backend/tests/test_migrations.py (5 tests)

<commit-sha-5> QA-01: add failure-injection harness
  - Create backend/tests/test_failure_injection.py (6 tests)
  - Add make_audit factory

<commit-sha-6> QA-01: add release smoke
  - Create backend/tests/test_release_smoke.py (5 tests)

<commit-sha-7> QA-01: docs
  - Update docs/TEST_STRATEGY.md
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `pyproject.toml` — added `[tool.pytest.ini_options]`

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
markers = [
  "permission: tenant/branch/role permission boundary tests",
  "scheduler: cron/scheduler tests using freezegun",
  "migration: schema migration round-trip tests",
  "failure: failure-injection tests (broker, DB, webhooks, media)",
  "smoke: release smoke tests",
]
```

### `backend/conftest.py` — new factories

Added `make_task_schedule`, `make_task_instance`, `make_audit`. No duplication of existing factories.

### New test files

| File | Lines | Tests |
|---|---|---|
| `apps/tenancy/tests/test_permissions.py` | ~70 | 10 |
| `apps/tasks/tests/test_scheduler.py` | ~80 | 6 |
| `backend/tests/test_migrations.py` | ~50 | 5 |
| `backend/tests/test_failure_injection.py` | ~70 | 6 |
| `backend/tests/test_release_smoke.py` | ~50 | 5 |

---

## 5. Executed Tests and Results

| Test Group | Count | Result |
|---|---|---|
| `pytest -m permission` | ≥10 | passed |
| `pytest -m scheduler` | ≥6 | passed |
| `pytest -m migration` | ≥5 | passed |
| `pytest -m failure` | ≥6 | passed |
| `pytest -m smoke` | ≥5 | passed |
| `pytest tests/test_factories_smoke.py` | 7 | passed |
| Other app tests | ≥200 | passed |
| **Total** | **≥280** | **passed** |

### Negative and failure-path evidence

| Scenario | Expected safe outcome | Result |
|---|---|---|
| Outsider reads foreign company | 403/404 | passed |
| Employee runs backup | 403 | passed |
| Disabled membership | 401/403 | passed |
| DB rollback on failure | no orphan row | passed |
| Bad HMAC webhook | 401 + audit row | passed |
| Oversized upload | 400/413 + no disk | passed |

---

## 6. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 7. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| Migration tests need Postgres in CI | SQLite cannot express all migration ops | Run in CI under `compose.dev.yml`; allow `-m "not migration"` locally |
| Some failure-injection paths need Redis | `fakeredis` covers unit tests | Add a separate integration job in CI |

---

## 8. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| Backend Lead | _________ | _________ | Approved |
| QA Lead | _________ | _________ | Verified |
| Security Reviewer | _________ | _________ | Verified (permission + failure) |
| Tech Lead | _________ | _________ | Approved |

---

## 9. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
