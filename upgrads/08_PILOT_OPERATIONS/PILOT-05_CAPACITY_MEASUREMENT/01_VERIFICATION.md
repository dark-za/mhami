# PILOT-05: Verification Commands

## Phase 1: Pre-Fix

```bash
Select-String -Path infra backend -Pattern "pilot.*capacity|capacity.*pilot" -Recurse
# Expected: 0 or generic metrics only
```

## Phase 2: Post-Fix

```bash
Test-Path docs\pilot-evidence\05_CAPACITY_REPORT.md
# Expected: True

Test-Path infra\monitoring\pilot-capacity.yml
# Expected: True

Select-String -Path docs\pilot-evidence\05_CAPACITY_REPORT.md -Pattern "p95|CPU|memory|error"
# Expected: 4+ matches
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
