# QA-01: Test Strategy

> **Rule:** every test in this file must **actually execute** against the running test database; the count must be ≥280 once the implementation is complete.

## 1. Unit Tests (Domain Services + Policy)

### 1.1 Permission tests

```python
# backend/apps/tenancy/tests/test_permissions.py
# See 03_IMPLEMENTATION.md §2.1 for the full file.
```

**Marker:** `pytest.mark.permission`
**Expected count:** ≥10

### 1.2 Domain service tests

The existing factories enable lightweight unit tests of the policy layer
(e.g. `apps.tenancy.services.LegalAcceptance`, `apps.tasks.services.dispatch_due_jobs`).
**Expected count:** ≥30 across `tenancy`, `tasks`, `evidence`, `reviews`, `backups`, `exports`, `audit`, `notifications`.

---

## 2. Integration Tests (DB, Tx, Outbox, Jobs)

### 2.1 Scheduler (frozen time)

```python
# backend/apps/tasks/tests/test_scheduler.py
# See 03_IMPLEMENTATION.md §3.1 for the full file.
```

**Marker:** `pytest.mark.scheduler`
**Expected count:** ≥6

### 2.2 Outbox + audit

- `apps/audit/tests/test_outbox_dispatch.py` — ≥3 tests
- `apps/exports/tests/test_export_pipeline.py` — ≥4 tests
- `apps/backups/tests/test_backup_restore.py` — ≥3 tests (already present)

---

## 3. API Tests (Contracts, Errors, Auth)

These live under each app's `tests/test_api.py` and use the existing
`force_login_company` factory.

| App | File | Min tests |
|---|---|---|
| `tenancy` | `apps/tenancy/tests/test_api.py` | 6 |
| `identity` | `apps/identity/tests/test_api.py` | 5 |
| `tasks` | `apps/tasks/tests/test_api.py` | 5 |
| `evidence` | `apps/evidence/tests/test_api.py` | 5 |
| `reviews` | `apps/reviews/tests/test_api.py` | 5 |
| `backups` | `apps/backups/tests/test_api.py` | 4 |
| `exports` | `apps/exports/tests/test_api.py` | 4 |
| `notifications` | `apps/notifications/tests/test_api.py` | 3 |
| `audit` | `apps/audit/tests/test_api.py` | 3 |
| `ai_gateway` | `apps/ai_gateway/tests/test_api.py` | 3 |
| `connector_control` | `apps/connector_control/tests/test_api.py` | 3 |
| `pilot` | `apps/pilot/tests/test_api.py` | 4 |
| **Total** | | **≥50** |

---

## 4. Permission Tests (Tenant, Branch, Role)

Already covered by §1.1 with the `permission` marker.

---

## 5. Scheduler Tests (Frozen Time)

Already covered by §2.1 with the `scheduler` marker.

---

## 6. Media Tests (Signature, Size, Face)

`apps/evidence/tests/test_media.py` — ≥5 tests:

- Reject signature mismatch.
- Reject oversize.
- Reject mismatched MIME.
- Reject duplicate hash.
- Allow re-upload after explicit reset.

---

## 7. AI Tests (Fake + Contract)

`apps/ai_gateway/tests/test_ai_contract.py` — ≥4 tests:

- The fake provider returns deterministic responses.
- The contract test asserts the request payload matches `openapi.yml`.
- The contract test asserts the response shape matches `openapi.yml`.
- A timeout is treated as a soft failure and audited.

---

## 8. Chrome Browser Tests (Playwright)

Covered by **QA-03** with its own `04_TESTING.md`. Layer requirement: ≥30.

---

## 9. Security Tests

`backend/tests/test_security.py` — ≥10 tests:

- CSRF token required for state-changing requests.
- Cookies are `HttpOnly`, `Secure`, `SameSite=Lax`.
- HSTS header present in production.
- CSP header present in production.
- No `DJANGO_SECRET_KEY` fallback in `settings.py`.
- No default `AUDIT_HMAC_SECRET` in compose.
- `force_login_company` is not exposed in `urls.py`.
- API rate limit returns `429` after threshold.
- A user without a company in the session receives `401`.
- A disabled membership receives `403`.

---

## 10. Migration Tests

`backend/tests/test_migrations.py` — covered by QA-01 §4.1 with the `migration` marker. Count: ≥5.

---

## 11. Backup-Restore Tests

`apps/backups/tests/test_backup_restore.py` — already present, keep and extend to ≥6.

---

## 12. Failure-Injection Tests

`backend/tests/test_failure_injection.py` — covered by QA-01 §5.1 with the `failure` marker. Count: ≥6.

---

## 13. Release Smoke

`backend/tests/test_release_smoke.py` — covered by QA-01 §6.1 with the `smoke` marker. Count: ≥5.

---

## 4. Success Criteria

| Layer | Count Target |
|---|---|
| Unit | 80+ |
| Integration | 30+ |
| API | 50+ |
| Permission | 30+ |
| Scheduler | 15+ |
| Browser E2E | 30+ (QA-03) |
| Security | 20+ |
| Migration | 10+ |
| Failure-injection | 10+ |
| Smoke | 5+ |
| **Total** | **≥280** |

---

## 5. Run Tests

### 5.1 Fast feedback

```bash
cd backend
pytest -m "not slow"
```

### 5.2 Full suite

```bash
cd backend
pytest
```

### 5.3 By layer

```bash
cd backend
pytest -m permission -v
pytest -m scheduler -v
pytest -m migration -v
pytest -m failure -v
pytest -m smoke -v
```

### 5.4 With coverage (cross-checks QA-02)

```bash
cd backend
pytest --cov=apps --cov-report=term --cov-fail-under=85
```
