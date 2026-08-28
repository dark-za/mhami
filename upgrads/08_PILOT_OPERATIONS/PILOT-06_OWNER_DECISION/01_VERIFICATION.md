# PILOT-06: Verification Commands

## Phase 1: Pre-Fix

```bash
Get-ChildItem docs\pilot-evidence -Filter "*DECISION*"
# Expected: no decision template
```

## Phase 2: Post-Fix

```bash
Test-Path docs\pilot-evidence\06_OWNER_DECISION.md
# Expected: True

Select-String -Path docs\pilot-evidence\06_OWNER_DECISION.md -Pattern "expand|continue|remediate|stop"
# Expected: 4 matches

Select-String -Path docs\pilot-evidence\06_OWNER_DECISION.md -Pattern "Signature|UTC|conditions|Evidence"
# Expected: 4+ matches
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
