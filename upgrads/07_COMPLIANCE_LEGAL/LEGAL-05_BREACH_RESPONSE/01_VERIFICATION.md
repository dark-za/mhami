# LEGAL-05: Verification Commands

## Phase 1: Pre-Fix

```bash
Test-Path docs\BREACH_RESPONSE.md
# Expected: False
```

## Phase 2: Post-Fix

```bash
# 1. Document exists
Test-Path docs\BREACH_RESPONSE.md
# Expected: True

# 2. ≥3 severity levels
Select-String -Path docs\BREACH_RESPONSE.md -Pattern "Critical|High|Medium"
# Expected: ≥ 3

# 3. Response team
Select-String -Path docs\BREACH_RESPONSE.md -Pattern "Incident Commander|Security Lead|DPO"
# Expected: ≥ 3

# 4. Model
Select-String -Path backend\apps\compliance\models.py -Pattern "class BreachIncident"
# Expected: 1 match

# 5. Tests
cd backend
pytest apps/compliance/tests/test_breach.py -v
# Expected: ≥ 3 passed

# 6. Runbook link
Select-String -Path docs\runbooks\11_BREACH_DETECTED.md -Pattern "BREACH_RESPONSE"
# Expected: 1 match
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
