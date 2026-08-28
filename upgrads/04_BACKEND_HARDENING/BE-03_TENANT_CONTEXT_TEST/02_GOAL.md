# BE-03: Comprehensive Tenant Isolation Tests — Goal

## Objective
Pin every cross-tenant boundary with an automated test so the
permission layer cannot regress without a CI failure.

## Acceptance criteria
1. `backend/tests/test_tenant_isolation.py` contains tests for:
   - Tenancy context bootstrap
   - Task templates and instances
   - Evidence and issue threads
   - Review decisions
   - Branch and membership boundaries
2. Every test authenticates a user in company A and attempts an
   action against a record owned by company B. The response is
   4xx.
3. `pytest tests/test_tenant_isolation.py` exits 0.
