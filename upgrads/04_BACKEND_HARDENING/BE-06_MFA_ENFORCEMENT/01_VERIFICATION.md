# BE-06: Verification Commands

## Phase 1: Pre-Fix

```bash
# 1. Default is False
Select-String -Path backend\config\settings -Pattern "MFA_ENFORCEMENT_ENABLED" -Recurse
# Expected: present, default False in base/dev/test

# 2. compose.prod.yml doesn't force False
Select-String -Path compose.prod.yml -Pattern "MFA_ENFORCEMENT_ENABLED=False"
# Expected: 0 matches
```

## Phase 2: Post-Fix

```bash
# 1. Prod default True
Select-String -Path backend\config\settings\prod.py -Pattern "MFA_ENFORCEMENT_ENABLED = True"
# Expected: 1 match

# 2. Dev default False
Select-String -Path backend\config\settings\dev.py -Pattern "MFA_ENFORCEMENT_ENABLED = False"
# Expected: 1 match

# 3. Middleware is registered
Select-String -Path backend\config\settings\base.py -Pattern "MFAEnforcementMiddleware"
# Expected: 1+ match

# 4. Tests pass
cd backend
pytest apps/identity/tests/test_mfa_enforcement.py -v
# Expected: ≥ 5 passed

# 5. State-changing endpoint from unenrolled Owner is 403
cd backend
pytest apps/identity/tests/test_mfa_enforcement.py::test_state_changing_blocked_when_unenrolled -v
# Expected: passed
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
