# LEGAL-02: Verification Commands

## Phase 1: Pre-Fix

```bash
Test-Path docs\ROPA.md
# Expected: False

Select-String -Path backend\apps -Pattern "ProcessingActivity" -Recurse
# Expected: 0 matches
```

## Phase 2: Post-Fix

```bash
# 1. ROPA exists with ≥10 activities
Select-String -Path docs\ROPA.md -Pattern "^## Activity" | Measure-Object | Select-Object -ExpandProperty Count
# Expected: ≥ 10

# 2. Model exists
Select-String -Path backend\apps\compliance\models.py -Pattern "class ProcessingActivity"
# Expected: 1 match

# 3. API endpoint
curl -fsS http://localhost:8000/api/v1/compliance/ropa/ | jq '.results | length'
# Expected: ≥ 10

# 4. Quarterly reminder
Select-String -Path backend\apps -Pattern "quarterly.*ropa|ROPA_REVIEW" -Recurse
# Expected: 1+ match
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
