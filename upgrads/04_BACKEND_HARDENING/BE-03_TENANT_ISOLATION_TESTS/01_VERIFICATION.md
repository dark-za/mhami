# BE-03: Verification Commands

## Phase 1: Pre-Fix

```bash
Get-ChildItem backend -Recurse -Filter test_tenant_isolation.py
# Expected: 0 or partial
pytest -m permission --collect-only -q | Select-Object -Last 2
# Expected: < 30
```

## Phase 2: Post-Fix

```bash
Test-Path backend\tests\test_tenant_isolation.py
# Expected: True

pytest -m permission --collect-only -q | Select-Object -Last 2
# Expected: ≥ 50

pytest -m permission
echo "Exit code: $LASTEXITCODE"
# Expected: 0

pytest -m "not slow" -q
# Expected: green
```

## Phase 3: Regression

```bash
pytest -m "not slow" -q
# Expected: green
```
