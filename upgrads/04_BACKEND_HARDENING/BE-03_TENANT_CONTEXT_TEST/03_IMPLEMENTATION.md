# BE-03: Comprehensive Tenant Isolation Tests — Implementation

## Files added
- `backend/tests/test_tenant_isolation.py` — 10 tests grouped by
  surface (context, tasks, evidence, reviews, branches).

## Approach
1. Reuse the conftest factories (`make_user`, `make_company`,
   `make_membership`, `make_template`, `force_login_company`, etc.)
   so the test surface is concise and consistent.
2. Every test follows the same shape: create company A, create
   company B, log in to A, attempt to read or mutate a record that
   belongs to B, assert the response is 4xx.
3. Owner-role users enroll MFA in-test so the BE-06 enforcement
   middleware does not block the test.
4. Acceptable response codes are 400, 403, or 404. Any 200 is a
   regression.
