# BE-03: Comprehensive Tenant Isolation Tests — Verification

## Evidence
- `backend/tests/test_tenant_isolation.py` is the canonical test
  module for cross-tenant boundaries. It groups tests into:
  - `TestTenancyContext` — bootstrap and session switching
  - `TestTaskIsolation` — task templates and instances
  - `TestEvidenceIsolation` — evidence and issue threads
  - `TestReviewIsolation` — review decisions
  - `TestBranchIsolation` — branch and membership boundaries

## Test result

```
$ pytest tests/test_tenant_isolation.py -q
..........                                                               [100%]
============================== warnings summary ===============================
...
10 passed, 1 warning in 28.14s
```

## Acceptance criteria
| ID | Criterion | Status |
|---|---|---|
| AC-1 | 10+ tenant isolation tests | ✅ (10 tests) |
| AC-2 | Tests pass locally | ✅ |
| AC-3 | Tests use the conftest factories | ✅ |
| AC-4 | Tests assert 4xx for cross-tenant access | ✅ |
