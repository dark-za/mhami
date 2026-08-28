# BE-02: Verification Commands

> **Instructions:** Run baseline (Phase 1) before, then post-fix (Phase 2) to confirm every serializer with an external ID calls the helper.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Count serializers with external IDs

```bash
Get-ChildItem backend/apps -Recurse -Filter serializers.py | ForEach-Object {
  Select-String $_ -Pattern "PrimaryKeyRelatedField|UUIDField"
} | Measure-Object | Select-Object -ExpandProperty Count
# Expected today: many
```

### Command 1.2 — Count calls to `validate_company_reference`

```bash
Select-String -Path backend/apps -Pattern "validate_company_reference" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
# Expected today: ~1 (only WeeklyShift)
```

### Command 1.3 — Cross-tenant reference tests

```bash
Get-ChildItem backend/apps -Recurse -Filter "test_*.py" | ForEach-Object {
  Select-String $_ -Pattern "cross.?tenant|foreign.?company"
} | Measure-Object | Select-Object -ExpandProperty Count
# Expected today: ~4
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — Every external-ID serializer calls the helper

```bash
# Run the audit script
cd backend
python scripts/ci/audit_serializer_validation.py
echo "Exit code: $LASTEXITCODE"
# Expected: 0 (every serializer that takes an external ID calls the helper)
```

### Command 2.2 — Cross-tenant tests ≥ 20

```bash
cd backend
pytest -k "cross_tenant or foreign_company" --collect-only -q | Select-Object -Last 2
# Expected: ≥ 20 tests
```

### Command 2.3 — All cross-tenant tests pass

```bash
cd backend
pytest -k "cross_tenant or foreign_company" -v
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### Command 2.4 — No regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```

### Command 2.5 — Threat model updated

```bash
Select-String -Path docs\SECURITY_THREAT_MODEL.md -Pattern "validate_company_reference"
# Expected: 1+ match
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Existing tests still pass

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```

### Command 3.2 — The helper rejects a foreign reference

```bash
cd backend
pytest apps/tenancy/tests/test_validate_company_reference.py -v
# Expected: passed
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 green
- ✅ Command 3.1 no regression
- ✅ Command 3.2 helper rejects foreign references
