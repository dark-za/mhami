# PILOT-01: Verification Commands

## Phase 1: Pre-Fix

```bash
Test-Path docs\pilot-evidence\01_CHARTER.md
# Expected: missing

Select-String -Path backend\apps -Pattern "PilotProgram" -Recurse
# Expected: 0
```

## Phase 2: Post-Fix

```bash
# 1. Template exists
Test-Path docs\pilot-evidence\01_CHARTER.md
# Expected: True

# 2. Model exists
Select-String -Path backend\apps\pilot\models.py -Pattern "class PilotProgram"
# Expected: 1 match

# 3. Fields
Select-String -Path backend\apps\pilot\models.py -Pattern "(company|owner_user|period|environment|scope|conditions)"
# Expected: 6+ matches

# 4. Signature link
Select-String -Path backend\apps\pilot -Pattern "C-06|owner_signature" -Recurse
# Expected: 1+ match
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
