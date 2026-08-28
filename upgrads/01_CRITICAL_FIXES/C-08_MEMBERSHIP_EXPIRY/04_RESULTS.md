# C-08: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Central active-membership predicate

`apps/tenancy/access.py` exposes a single `Q` expression that callers
must use instead of local `active=True` filters:

```python
# ``active_until``. Callers should prefer these helpers over a local
# `active=True` filter.
return Q(active_until__isnull=True) | Q(active_until__gt=timezone.now())
```

Every place that previously filtered on `CompanyMembership.active` or
`UserBranchMembership.active` alone now ANDs this predicate in:

- Auth / tenant context (`apps/tenancy/services.py`).
- Branch scope checks (C-07).
- Reviews (`apps/reviews/services.py`).
- Exports (`apps/exports/services.py`).
- Evidence task authorization.
- Scheduler — expired members no longer receive scheduled tasks.
- Support access — `current_support_authorization` honours the same
  expiry.

### Session lifetime

The auth backend revokes the session when the underlying user is
disabled (`is_active=False`) or when the active company membership is
`active=False` / `active_until <= now`. A disabled user cannot create a
new session, and an existing session is rejected on the next request
through a 401 with an explicit "session-expired" envelope.

### Tests

- `apps/tenancy/tests/test_access.py` covers the boundary cases:
  company expiry, branch expiry, support expiry, and the
  `disabled = active=False` case.
- `apps/identity/tests/test_auth.py` covers session reuse after expiry.
- Both suites run against PostgreSQL so the `active_until` timestamp
  comparisons exercise the real clock.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Shared `active=True AND (active_until IS NULL OR active_until > now)` predicate | PASS | `apps/tenancy/access.py` |
| AC-2 Auth, tenant, branch, reviews, exports, evidence, scheduler, support use it | PASS | Code references above |
| AC-3 Disabled user cannot create or use a session | PASS | `identity/tests/test_auth.py` |
| AC-4 Boundary-time tests for company/branch/support expiry and session reuse | PASS | `tenancy/tests/test_access.py` |
| AC-5 Indexes/migrations reviewed | PASS | `active_until` indexed on `CompanyMembership` and `UserBranchMembership` |

## Risks / Follow-ups

- A scheduled Celery task (C-11) periodically logs the count of
  near-expiry memberships so the pilot manager can revoke proactively.
