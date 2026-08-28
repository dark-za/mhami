# PILOT-04: Verification Commands

## Phase 1: Pre-Fix

```bash
Get-ChildItem docs\pilot-evidence -Filter "*usability*"
# Expected: no protocol
```

## Phase 2: Post-Fix

```bash
Test-Path docs\pilot-evidence\04_USABILITY_PROTOCOL.md
# Expected: True

Test-Path docs\pilot-evidence\04_USABILITY_FINDINGS.md
# Expected: True

Select-String -Path docs\pilot-evidence\04_USABILITY_FINDINGS.md -Pattern "Participant|Severity|Disposition"
# Expected: 3+ matches
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
