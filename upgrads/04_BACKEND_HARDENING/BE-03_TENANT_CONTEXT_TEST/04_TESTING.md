# BE-03: Comprehensive Tenant Isolation Tests — Testing

## Unit tests
- `backend/tests/test_tenant_isolation.py` — 10 tests covering
  tenancy context, task isolation, evidence isolation, review
  isolation, and branch isolation.

## Manual checklist
- [x] `pytest tests/test_tenant_isolation.py` exits 0
- [x] All tests use the conftest factories
- [x] All tests assert 4xx for cross-tenant access
