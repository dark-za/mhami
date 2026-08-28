# BE-05: Verification Commands

## Phase 1: Pre-Fix

```bash
Select-String -Path backend/apps -Pattern "record_login_failure|LOGIN_FAILED" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
# Expected today: 0
```

## Phase 2: Post-Fix

```bash
# 1. Helper exists
Select-String -Path backend/apps -Pattern "def record_login_failure" -Recurse
# Expected: 1+ match

# 2. Auth backend calls it
Select-String -Path backend\apps\tenancy\auth_backends.py -Pattern "record_login_failure"
# Expected: 3+ matches (company_not_found, invalid_credentials, company_unavailable)

# 3. Tests pass
cd backend
pytest apps/tenancy/tests/test_login_failure_audit.py -v
# Expected: 4-5 passed

# 4. LoginFailuresHigh alert
Select-String -Path infra/monitoring/prometheus/alerts/business.yml -Pattern "LoginFailuresHigh"
# Expected: 1 match
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
