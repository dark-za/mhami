# PILOT-02: Verification Commands

## Phase 1: Pre-Fix

```bash
Select-String -Path backend -Pattern "DailyLog" -Recurse
# Expected: 0
```

## Phase 2: Post-Fix

```bash
# 1. Model
Select-String -Path backend\apps\pilot\models.py -Pattern "class DailyLog"
# Expected: 1 match

# 2. Fields
Select-String -Path backend\apps\pilot\models.py -Pattern "(pilot_program|day|author|observed_issues|severity|actions_taken)"
# Expected: 6+ matches

# 3. Frontend
Test-Path frontend\src\pages\Pilot\DailyLog.tsx
# Expected: True
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
