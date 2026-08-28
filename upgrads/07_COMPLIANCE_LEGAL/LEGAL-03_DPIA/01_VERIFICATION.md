# LEGAL-03: Verification Commands

## Phase 1: Pre-Fix

```bash
Test-Path docs\DPIA.md
# Expected: False
```

## Phase 2: Post-Fix

```bash
# 1. DPIA exists
Test-Path docs\DPIA.md
# Expected: True

# 2. ≥4 activities
Select-String -Path docs\DPIA.md -Pattern "^## Activity"
# Expected: ≥ 4

# 3. Each has Description, Necessity, Risk, Mitigation, Consultation
Select-String -Path docs\DPIA.md -Pattern "^### (Description|Necessity|Risk|Mitigation|Consultation)"
# Expected: ≥ 20 (4 activities × 5 sections)

# 4. Model exists
Select-String -Path backend\apps\compliance\models.py -Pattern "class DPIARisk"
# Expected: 1 match

# 5. Annual reminder
Select-String -Path backend\apps -Pattern "annual.*dpia|DPIA_REVIEW_DUE" -Recurse
# Expected: 1+ match
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
