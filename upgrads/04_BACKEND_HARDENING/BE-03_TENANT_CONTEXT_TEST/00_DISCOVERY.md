# BE-03: Comprehensive Tenant Isolation Tests

## Discovery

### Current state (as-is)
- `backend/tests/test_tenant_isolation.py` already exists and covers
  tenancy context, tasks, evidence, reviews, and branch isolation.
- 10 tests pass in the current suite.

### What is missing
- A scheduler test (a tenant boundary must hold when the
  background scheduler pulls in cross-tenant data via a generic
  queryset).
- A backup / restore test that confirms a backup of company A is
  restored only inside company A.
- An export test that confirms the export service refuses to
  emit records for companies other than the active one.

## Acceptance criteria
- 10+ tests in `tests/test_tenant_isolation.py` already pass.
- All new tests follow the same pattern: an authenticated user in
  company A attempts to read/mutate a record owned by company B;
  the response is 4xx.
- `pytest tests/test_tenant_isolation.py` exits 0.
