# PILOT-03: Verification Commands

## Phase 1: Pre-Fix

```bash
Select-String -Path backend -Pattern "WeeklyReport" -Recurse
# Expected: 0
```

## Phase 2: Post-Fix

```bash
Select-String -Path backend\apps\pilot\models.py -Pattern "class WeeklyReport"
# Expected: 1 match

Test-Path backend\apps\pilot\reports\weekly.py
# Expected: True
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
