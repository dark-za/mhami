# C-12: Enforce Task Transfer Invariants

## Discovery

Transfer approval can retain the old executor state and allows races between
pending requests:

- `backend/apps/tasks/services.py:237-270`
- `backend/apps/tasks/api/views.py:204-221`

The target user is not proven to hold active branch access at approval time,
and terminal or concurrent transfer requests need explicit policy.

## Goal

Create one locked transfer state machine that preserves assignment, execution,
and audit invariants.

## Acceptance Criteria

1. Request and approval lock the task and relevant pending transfer records.
2. Only one pending transfer is allowed per task unless an approved replacement
   policy is implemented.
3. Approval clears prior claim/start state, verifies target branch membership
   at the effective time, and rejects terminal/ineligible tasks.
4. Authorization is checked before mutation and all transitions are auditable.
5. PostgreSQL concurrency tests cover competing requests/approvals, old-user
   completion attempts, target expiry, and cross-branch targets.

## Required Evidence

- State-transition table.
- Concurrent PostgreSQL test output.
- Product and Security approval.
