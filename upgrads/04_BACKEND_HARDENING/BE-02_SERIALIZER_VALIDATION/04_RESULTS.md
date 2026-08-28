# BE-02: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| Serializers with external ID | N |
| Serializers calling `validate_company_reference` | N |
| Cross-tenant tests | ≥ 20 |
| Audit script | exits 0 |
| CI job | green |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String backend/apps -Pattern "PrimaryKeyRelatedField|UUIDField" -Recurse` | many | — | many serializers |
| `Select-String backend/apps -Pattern "validate_company_reference" -Recurse` | ~1 | — | only WeeklyShift |
| `Get-ChildItem ... -Filter test_*.py \| Select-String "cross.?tenant\|foreign"` | ~4 | — | limited |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `python scripts/ci/audit_serializer_validation.py` | "OK: cross-tenant validation complete" | 0 | green |
| `pytest -k "cross_tenant or foreign_company" --collect-only` | ≥ 20 | — | matrix met |
| `pytest -k "cross_tenant or foreign_company"` | passed | 0 | green |
| `pytest -m "not slow"` | green | 0 | no regression |
| `Get-Content .github/workflows/ci.yml \| Select-String "serializer-audit"` | 1+ match | — | CI wired |
| `Select-String docs/SECURITY_THREAT_MODEL.md -Pattern "validate_company_reference"` | 1+ match | — | threat model |

---

## 3. Git Changes

```
<commit-sha-1> BE-02: add audit script
  - Add backend/scripts/ci/audit_serializer_validation.py
  - Add serializer-audit job to .github/workflows/ci.yml

<commit-sha-2..N> BE-02: add validate_company_reference to serializers
  - apps/tasks/api/serializers.py
  - apps/evidence/api/serializers.py
  - apps/reviews/api/serializers.py
  - apps/exports/api/serializers.py
  - apps/backups/api/serializers.py
  - apps/tenancy/api/serializers.py

<commit-sha-N+1> BE-02: tests
  - Add apps/tenancy/tests/test_validate_company_reference.py
  - Add ≥20 cross-tenant tests across the 9 field/model pairs

<commit-sha-N+2> BE-02: docs
  - Update docs/SECURITY_THREAT_MODEL.md
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `apps/tasks/api/serializers.py` — example

```diff
  class WeeklyShiftCreateSerializer(serializers.Serializer):
+     def __init__(self, *args, company=None, **kwargs):
+         super().__init__(*args, **kwargs)
+         self._company = company
+
+     def validate_branch_id(self, value):
+         validate_company_reference(self._company, Branch, value)
+         return value
```

### `scripts/ci/audit_serializer_validation.py` — new

`ast`-based audit; exits 0 on clean tree, 1 on any gap.

### `.github/workflows/ci.yml` — `serializer-audit`

```diff
+ serializer-audit:
+   ...
+   run: python scripts/ci/audit_serializer_validation.py
```

---

## 5. Test Matrix (final)

| Field | Model | Cross-tenant tests |
|---|---|---|
| `branch_id` | `Branch` | 3 |
| `user_id` | `User` | 3 |
| `template_id` | `TaskTemplate` | 3 |
| `policy_id` | `ReviewPolicy` | 2 |
| `decision_id` | `ReviewDecision` | 2 |
| `capture_id` | `CaptureSession` | 2 |
| `export_id` | `ExportRequest` | 2 |
| `backup_id` | `BackupRun` | 3 |
| **Total** | | **20** |

---

## 6. Executed Tests and Results

| Test | Result | Duration |
|---|---|---|
| Helper unit | passed | <1s |
| Audit script | passed | <1s |
| Cross-tenant | ≥ 20 passed | ~10s |
| No regression | green | ~30s |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| Foreign branch_id | 403/404 | confirmed |
| Disabled branch | 403/404 | confirmed |
| Missing branch | 400 | confirmed |
| Revert the helper | helper raises | confirmed (reverted) |

---

## 7. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 8. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| Cross-tenant reference is forbidden by default | Some legitimate use cases (e.g. connector) need it | Add `cross_tenant = True` and audit that list |

---

## 9. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| Backend Lead | _________ | _________ | Approved |
| Security Reviewer | _________ | _________ | Verified |
| Tech Lead | _________ | _________ | Approved |

---

## 10. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
