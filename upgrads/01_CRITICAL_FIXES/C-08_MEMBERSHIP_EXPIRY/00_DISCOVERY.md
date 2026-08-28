# C-08: Enforce Membership Expiry and Revocation

## Discovery

Company and branch memberships carry `active_until`, but access code generally
checks only `active=True`:

- `backend/apps/organizations/models.py:52-74`
- `backend/apps/tenancy/access.py:44-64`

An expired member can retain company, branch, review, evidence, and export
access until an operator changes `active` manually.

## Goal

Make expiry and revocation enforceable at one central access boundary and
prevent stale sessions from retaining effective authorization.

## Acceptance Criteria

1. A shared active-membership predicate requires `active=True` and an empty or
   future `active_until` value.
2. Auth, tenant context, branch scope, reviews, exports, evidence, scheduler,
   and support use that predicate rather than local `active=True` filters.
3. A disabled user cannot create a session or use an existing one.
4. Boundary-time tests cover company and branch expiry, revocation, support
   expiry, and session reuse on PostgreSQL.
5. Required indexes/migrations are reviewed for time-based access queries.

## Required Evidence

- Authorization matrix with expiry behavior.
- Browser and API negative tests.
- Security reviewer sign-off.
