# QA-01: Implement All Test Layers

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The repository has only a smoke test (`backend/tests/test_factories_smoke.py`) that confirms factories work. The 12 test layers defined in `docs/TEST_STRATEGY.md` are **mostly missing** (unit, integration, API tests are partial; permission, scheduler, browser, migration, failure-injection, and smoke tests are absent).

**Evidence gathered:**
- `backend/tests/` directory contains only:
  ```
  README.md
  test_factories_smoke.py
  __pycache__/
  ```
- Per `docs/TEST_STRATEGY.md` and `PHASE12_DEFECT_DISPOSITION.md`, only ~65 of the 280+ target tests exist (unit ~30, integration ~10, API ~20, others 0).
- The conftest at `backend/conftest.py` already exposes 9 reusable factories (`make_user`, `make_company`, `make_branch`, `make_membership`, `make_job_role`, `make_branch_membership`, `make_task_template`, `make_evidence`, `force_login_company`) — these are the **foundation** for the missing tests.
- Frontend has `vitest` configured but no Playwright runner is installed (`package.json` shows no `@playwright/test`).

### Impact

| Dimension | Impact |
|---|---|
| Functional | Regressions in IDOR/RBAC/audit cannot be detected by CI; C-* and H-* fixes lack a regression safety net. |
| Security | Permission/scheduler/media tests are missing, so the controls listed in `SECURITY_THREAT_MODEL.md` are not exercised. |
| Operational | Gate-D/F release decisions cannot be evidence-based — there is no automated safety net. |
| Compliance | PDPL/PDPL-aligned audit assertions are not tested. |
| Financial | Re-work for undetected regressions during pilot. |

### Reproducible Evidence

```bash
# Count existing tests
cd backend
pytest --collect-only -q | Select-Object -Last 5
# Expected today: ~7 collected items (1 smoke file)

# Confirm Playwright is missing in frontend
Select-String -Path frontend\package.json -Pattern "@playwright"
# Expected today: 0 matches

# Confirm scheduler/permission test directories missing
Test-Path backend\apps\tenancy\tests\test_permissions.py
Test-Path backend\apps\tasks\tests\test_scheduler.py
# Expected today: False False
```

---

## 2. Gap

| Layer | Current | Target |
|---|---|---|
| Unit (domain services + policy) | ~30 | 80+ |
| Integration (DB constraints, tx, outbox, jobs) | ~10 | 30+ |
| API (contracts, errors, auth) | ~20 | 50+ |
| Permission (tenant, branch, role) | 0 | 30+ |
| Scheduler (frozen time) | 0 | 15+ |
| Media (signature, size, face) | partial | full |
| AI (fake + contract) | partial | full |
| Chrome E2E (Playwright) | 0 | 30+ |
| Security | ~5 | 20+ |
| Migration | 0 | 10+ |
| Backup-restore (already present) | yes | keep |
| Failure-injection | 0 | 10+ |
| Release smoke | 0 | 5+ |
| **Total** | **~65** | **280+** |

---

## 3. Goal Statement

> Within **2 weeks**, implement the 12 test layers defined in `docs/TEST_STRATEGY.md` to reach a baseline of **280+ tests** that exercise the existing factories, the tenancy/permission boundary, the scheduler with frozen time, the migration safety net, the failure-injection harness, and a release smoke flow.

### Acceptance Criteria

1. **AC-1:** `pytest --collect-only` returns ≥280 tests across the 12 layers.
2. **AC-2:** A permission test file (≥10 tests) blocks cross-tenant, cross-branch, and role-mismatch access for at least 5 endpoints.
3. **AC-3:** A scheduler test file (≥6 tests) uses `freezegun` to verify that scheduled jobs fire at the right wall clock, respect grace windows, and skip duplicates.
4. **AC-4:** A migration test file (≥5 tests) runs `migrate` and `migrate <previous>` against a temporary DB and asserts no data loss for tenants, branches, memberships, and tasks.
5. **AC-5:** A failure-injection test file (≥6 tests) simulates broker outage, DB disconnect, malformed webhook, expired HMAC, oversized payload, and missing media — all producing safe, audited failures.
6. **AC-6:** A release smoke test (≥5 tests) boots the app via Django check + DRF schema + a representative happy-path call for each app.
7. **AC-7:** All new tests pass on a clean `pytest` run (exit code 0).
8. **AC-8:** Tests are organised under `apps/<app>/tests/` using the existing factories; no parallel fixture definitions.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hidden coupling between factories and tests | Medium | High | Rely on the existing `make_*` factories; do not duplicate them. |
| Tests become slow (>5 min) | Medium | Medium | Mark layers with `pytest.mark.integration` / `pytest.mark.slow`; keep unit tests fast. |
| Scheduler tests become flaky | Medium | High | Use `freezegun.freeze_time` everywhere; avoid `time.sleep`. |
| Migration tests need a real Postgres | Low | High | Run in CI under the existing `compose.dev.yml`; for local dev skip with `-m "not migration"`. |
| Permission tests miss a guard | Medium | High | Cross-reference `SECURITY_THREAT_MODEL.md` per endpoint. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `pytest.mark.*` markers in `pyproject.toml` | QA Lead | not-started |
| 2 | Write `apps/tenancy/tests/test_permissions.py` (≥10) | Backend | not-started |
| 3 | Write `apps/tasks/tests/test_scheduler.py` (≥6) with `freezegun` | Backend | not-started |
| 4 | Write `backend/tests/test_migrations.py` (≥5) using `django.test.utils.captured_stdout` | Backend | not-started |
| 5 | Write `backend/tests/test_failure_injection.py` (≥6) | Backend | not-started |
| 6 | Write `backend/tests/test_release_smoke.py` (≥5) | Backend | not-started |
| 7 | Run `pytest --collect-only` and assert ≥280 | QA Lead | not-started |
| 8 | Run `pytest` and assert exit 0 | QA Lead | not-started |
| 9 | Update `docs/TEST_STRATEGY.md` with the new test files | Tech Writer | not-started |
| 10 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [docs/TEST_STRATEGY.md](../../../docs/TEST_STRATEGY.md)
- [backend/conftest.py](../../../backend/conftest.py) — factories
- [backend/pyproject.toml](../../../backend/pyproject.toml) — markers + deps
- [docs/SECURITY_THREAT_MODEL.md](../../../docs/SECURITY_THREAT_MODEL.md)
- [upgrads/01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT](../01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT/00_DISCOVERY.md) — pattern for permission tests
