# H-02: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Class-level RBAC enforcement

`backend/apps/reviews/api/views.py:43-...` declares the
`ReviewPolicyView` with `required_roles = (CompanyRole.OWNER,)` at
class level. The mixin `TenantAPIView` evaluates this attribute
**before** the handler runs, so an employee or monitor request is
rejected with 403 before any business logic executes.

### Why a class-level check

The previous design did the role check inside `patch()` via a
`CompanyMembership` lookup. That was both a defense-in-depth gap and a
performance pitfall (one extra DB hit per request, plus a chance to
forget the check on a new method). The class-level attribute is now
the single source of truth.

### Tests

`backend/apps/reviews/tests/test_policy_rbac.py` covers:

- `test_employee_cannot_patch_policy` — 403 returned, no policy row
  mutated, no audit event recorded.
- `test_monitor_cannot_patch_policy` — same outcome.
- `test_owner_can_patch_policy` — happy path, audit event
  `REVIEW_POLICY_UPDATED` recorded.
- `test_employee_can_get_policy` — the GET path is still readable for
  non-owners; only mutation is restricted.

The tests run against PostgreSQL so the role lookup exercises the
real `CompanyMembership.role` enum and the same `select_for_update`
path the API uses.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Employee and Monitor get 403 early | PASS | `test_employee_cannot_patch_policy`, `test_monitor_cannot_patch_policy` |
| AC-2 Owner only can PATCH | PASS | `test_owner_can_patch_policy` |
| AC-3 No regression in GET | PASS | `test_employee_can_get_policy` |

## Risks / Follow-ups

- Any future addition to `ReviewPolicyView` (e.g. `delete` or
  `create_version`) inherits the same RBAC automatically; this is the
  intended behaviour of the class-level check.
