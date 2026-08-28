# BE-02: Strengthen Cross-Tenant Serializer Validation

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** Several serializers accept external IDs (e.g. `branch_id`, `user_id`, `template_id`) and resolve them by `.get(pk=...)` without asserting the record belongs to the active company. The C-03 fix added a `validate()` in `WeeklyShiftCreateSerializer` that calls a helper, but the same pattern must be applied to every serializer that takes an external ID.

**Evidence gathered:**

```bash
# 1. List serializers that take external IDs
Get-ChildItem backend/apps -Recurse -Filter serializers.py |
  ForEach-Object { Select-String $_ -Pattern "PrimaryKeyRelatedField|UUIDField" }
# Expected: many hits

# 2. Find serializers that do NOT call a tenant helper
Select-String -Path backend/apps -Pattern "validate_company_reference" -Recurse
# Expected today: only the WeeklyShift serializer
```

### Impact

| Dimension | Impact |
|---|---|
| Security | Cross-tenant reference forgery (a Company A user submits `branch_id=CompanyB_branch_id`) — IDOR. |
| Compliance | PDPL data minimization requires that the user cannot see or reference another tenant's data. |
| Operational | Hard-to-debug 500s when a referenced row is missing in the new tenant context. |

### Reproducible Evidence

```bash
# Find a serializer missing the helper
Select-String -Path backend/apps -Pattern "def validate_.*id" -Recurse
# Inspect each for `validate_company_reference` call
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `validate_company_reference` helper | present (`apps.tenancy.access`) | unchanged |
| Serializers that take an external ID and call the helper | 1 (WeeklyShift) | all of them |
| Tests that exercise cross-tenant reference forgery | 4 (per C-03) | ≥20 |

---

## 3. Goal Statement

> Within **1 week**, every serializer that accepts an external ID (e.g. `branch_id`, `user_id`, `template_id`, `policy_id`, `decision_id`, `capture_id`) calls `validate_company_reference(company, Model, value)` and the platform raises `PlatformPermissionException` on a foreign-tenant reference. Add **≥20 cross-tenant reference tests**.

### Acceptance Criteria

1. **AC-1:** `apps/tenancy/access.py::validate_company_reference` is the single helper.
2. **AC-2:** Every serializer in `apps/*/api/serializers.py` that takes an external ID calls the helper in its `validate_<field>` method.
3. **AC-3:** The helper raises `PlatformPermissionException` on a foreign-tenant reference.
4. **AC-4:** A foreign-tenant reference test exists for at least 20 serializer/field combinations.
5. **AC-5:** The CI runs the cross-tenant test suite on every PR.
6. **AC-6:** No regression in existing tests.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A serializer legitimately accepts a cross-tenant reference (e.g. a connector that talks to another tenant) | Low | High | Allow opt-out via a per-serializer class attribute `cross_tenant = True` and audit that list |
| Performance regression | Low | Low | The helper is a single indexed query |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Confirm `validate_company_reference` is in `apps/tenancy/access.py` | Backend | not-started |
| 2 | Enumerate every serializer with an external ID | Backend | not-started |
| 3 | Add `validate_company_reference` calls | Backend | not-started |
| 4 | Add ≥20 cross-tenant reference tests | Backend | not-started |
| 5 | Update `docs/SECURITY_THREAT_MODEL.md` | Security Lead | not-started |
| 6 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT](../../01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT/00_DISCOVERY.md)
- [upgrads/04_BACKEND_HARDENING/BE-01_RBAC_AUDIT](..) — class-level guard
- [upgrads/04_BACKEND_HARDENING/BE-03_TENANT_ISOLATION_TESTS](..) — the test layer
