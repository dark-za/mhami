# BE-03: Comprehensive Tenant Isolation Tests

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The QA-01 test plan calls for **tenant / branch / role permission tests** (`pytest.mark.permission`, ≥30). The C-03 fix added 4 IDOR tests for `WeeklyShift`, the C-07 fix added branch-scope tests for `EvidenceItem`, and BE-01's audit script + BE-02's cross-tenant serializer helper close the class- and field-level gaps. A **dedicated tenant-isolation test suite** still needs to wire it all together and exercise every endpoint that takes an external ID.

**Evidence gathered:**

```bash
# 1. Count existing permission/tenant tests
Get-ChildItem backend/apps -Recurse -Filter "test_*.py" | ForEach-Object {
  Select-String $_ -Pattern "tenant|isolation|branch"
} | Measure-Object | Select-Object -ExpandProperty Count
# Expected today: limited
```

### Impact

| Dimension | Impact |
|---|---|
| Security | A regression in any serializer/view can re-introduce IDOR. |
| Compliance | Gate-D requires automated evidence of isolation. |
| Operational | Catch IDOR before pilot. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Dedicated `test_tenant_isolation.py` | partial | full |
| Tests per endpoint | 1-2 | ≥5 |
| Cross-tenant | partial | full |
| Cross-branch | partial | full |
| Role matrix | partial | full |

---

## 3. Goal Statement

> Within **1 week**, write a dedicated `backend/tests/test_tenant_isolation.py` with **≥50 tests** covering cross-tenant, cross-branch, role mismatch, and disabled membership for every endpoint that takes an external ID.

### Acceptance Criteria

1. **AC-1:** `backend/tests/test_tenant_isolation.py` exists with ≥50 tests.
2. **AC-2:** Each endpoint listed in `BE-02` has ≥5 tests (happy + 4 negative).
3. **AC-3:** Tests cover: cross-tenant, cross-branch, role mismatch, disabled membership, missing company in session.
4. **AC-4:** All tests pass on a clean run.
5. **AC-5:** Tests run in the existing `pytest -m permission` invocation.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Tests become slow | Medium | Medium | Use the `make_*` factories; mark slow tests |
| Tests become flaky | Low | High | Use `force_login_company`; no real auth |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Inventory every endpoint that takes an external ID | Backend | not-started |
| 2 | Write the test file | Backend | not-started |
| 3 | Add `permission` marker (already done in QA-01) | QA Lead | not-started |
| 4 | Run `pytest -m permission` | Backend | not-started |
| 5 | Update `docs/TEST_STRATEGY.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT](../../01_CRITICAL_FIXES/C-03_IDOR_WEEKLYSHIFT/00_DISCOVERY.md)
- [upgrads/04_BACKEND_HARDENING/BE-01_RBAC_AUDIT](..)
- [upgrads/04_BACKEND_HARDENING/BE-02_SERIALIZER_VALIDATION](..)
- [upgrads/06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS](../06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS/00_DISCOVERY.md) — markers
