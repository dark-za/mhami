# BE-06: Test Strategy

> **Rule:** every privileged user without MFA is blocked from state-changing requests.

## 1. Unit Tests

```bash
cd backend
pytest apps/identity/tests/test_mfa_enforcement.py -v
# Expected: 5 passed
```

## 2. Integration Tests

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Frontend redirect

After the backend returns 403 with `detail: "MFA enrollment required"`, the frontend redirects to `/mfa/enroll`.

```bash
cd frontend
npx playwright test tests/e2e/08_mfa.spec.ts --reporter=line
# Expected: passed
```

### 3.2 Recovery code

```bash
cd backend
pytest apps/identity/tests/test_mfa_recovery.py -v
# Expected: passed
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| `test_enrolled_user_can_post` | 200/405 |
| `test_unenrolled_owner_cannot_post` | 403 |
| `test_unenrolled_owner_can_get` | 200 |
| `test_unenrolled_employee_can_post` | 200/405 |
| `test_staff_user_required_to_have_mfa` | 403 |
| E2E redirect | passed |

## 5. Cross-links

- [upgrads/03_FRONTEND_REBUILD/FE-04_WORKFLOW_SCREENS](../../03_FRONTEND_REBUILD/FE-04_WORKFLOW_SCREENS/00_DISCOVERY.md) — enrollment UI
- [upgrads/04_BACKEND_HARDENING/BE-01_RBAC_AUDIT](..) — class-level guard
