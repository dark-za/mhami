# LEGAL-01: Verification Commands

## Phase 1: Pre-Fix

```bash
Get-ChildItem docs\legal -Recurse -Filter "*.md"
# Expected today: only README.md + 08_TEMPLATES

Select-String -Path docs\legal -Pattern "approved|counsel|signed" -Recurse
# Expected today: 0 matches
```

## Phase 2: Post-Fix

```bash
# 1. All 7 documents exist
Get-ChildItem docs\legal -Recurse -Filter "v1.0.md"
# Expected: 7 folders × (en + ar) = 14 files

# 2. Each has a counsel sign-off line
Select-String -Path docs\legal -Pattern "Counsel approval|approved by" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
# Expected: ≥ 7

# 3. LegalAcceptance flow
cd backend
pytest apps/compliance/tests/test_legal_acceptance.py -v
# Expected: ≥ 3 passed

# 4. Re-acceptance on update
pytest apps/compliance/tests/test_legal_reacceptance.py -v
# Expected: passed

# 5. CHANGELOG
Select-String -Path CHANGELOG.md -Pattern "LEGAL-01"
# Expected: 1+ match
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
