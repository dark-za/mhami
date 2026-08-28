# BE-02: Test Strategy

> **Rule:** every cross-tenant reference test must pass on a real backend with a real second tenant.

## 1. Unit Tests

### 1.1 `validate_company_reference` helper

```bash
cd backend
pytest apps/tenancy/tests/test_validate_company_reference.py -v
# Expected: 2-3 passed
```

### 1.2 Audit script

```bash
cd backend
python scripts/ci/audit_serializer_validation.py
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## 2. Integration Tests

### 2.1 Per-serializer cross-tenant reference tests

| Field | Model | Test |
|---|---|---|
| `branch_id` | `Branch` | 3 tests |
| `user_id` | `User` | 3 tests |
| `template_id` | `TaskTemplate` | 3 tests |
| `policy_id` | `ReviewPolicy` | 2 tests |
| `decision_id` | `ReviewDecision` | 2 tests |
| `capture_id` | `CaptureSession` | 2 tests |
| `export_id` | `ExportRequest` | 2 tests |
| `backup_id` | `BackupRun` | 3 tests |
| **Total** | | **20** |

```bash
cd backend
pytest -k "cross_tenant or foreign_company" --collect-only -q | Select-Object -Last 2
# Expected: ≥ 20
pytest -k "cross_tenant or foreign_company"
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## 3. End-to-End Tests

### 3.1 Audit script in CI

```bash
Get-Content .github/workflows/ci.yml | Select-String -Pattern "serializer-audit"
# Expected: 1+ match
```

### 3.2 Threat model

```bash
Select-String -Path docs/SECURITY_THREAT_MODEL.md -Pattern "validate_company_reference"
# Expected: 1+ match
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| Helper unit | 2-3 | passed |
| Audit script | 1 | exit 0 |
| Per-field cross-tenant | 20 | passed |
| No regression | N | green |
| CI job | 1 | present |
| Threat model | 1 | updated |

---

## 5. Run Tests

### 5.1 Local

```bash
cd backend
python scripts/ci/audit_serializer_validation.py
pytest apps/tenancy/tests/test_validate_company_reference.py -v
pytest -k "cross_tenant or foreign_company" -v
```

### 5.2 CI

The `serializer-audit` job runs on every PR. The cross-tenant tests run in the existing `backend` job.

### 5.3 Failure simulation

| Scenario | Expected |
|---|---|
| Add a serializer with an `_id` field but no `validate_company_reference` | exit 1 |
| Submit a foreign-tenant ID via API | 403/404 |
| Revert the helper | helper raises |

---

## 6. Cross-links

- [upgrads/01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT](../../01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT/00_DISCOVERY.md)
- [upgrads/04_BACKEND_HARDENING/BE-01_RBAC_AUDIT](..)
- [upgrads/04_BACKEND_HARDENING/BE-03_TENANT_ISOLATION_TESTS](..)
