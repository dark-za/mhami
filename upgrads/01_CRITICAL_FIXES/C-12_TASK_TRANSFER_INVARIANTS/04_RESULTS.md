# C-12: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Locked state machine

`apps/tasks/services.py:238-...` exposes `request_transfer` and
`resolve_transfer`. Both paths are wrapped in
`select_for_update()` on the parent `TaskInstance` and the
`TaskTransferRequest` row, so two concurrent operations cannot
collide.

### Single pending transfer

The model is annotated with a partial unique constraint
(`status = "pending"`) so the database itself rejects a second
pending transfer for the same task. The negative test
`apps/tasks/tests/test_transfer.py::test_second_pending_rejected`
asserts the `IntegrityError` surfaces as a 409 from the API.

### Approval invariants

`resolve_transfer` performs the following checks before flipping the
state to `APPROVED`:

1. Target user still holds an **active** membership in the task's
   company at the time of resolution.
2. Target user has an **active** branch membership for the task's
   branch at the time of resolution.
3. The task is not in a terminal state (e.g. cancelled or
   auto-closed).
4. Any prior claim / start state on the task is cleared and an audit
   event records the transition.

The state-transition table is documented in
`apps/tasks/TRANSFER_STATE_MACHINE.md`.

### Concurrency tests

`apps/tasks/tests/test_transfer_concurrency.py` covers:

- Competing requesters for the same task — only one wins.
- Competing approvers — only the first call flips the state.
- Old user attempts to complete the task after the transfer is
  approved — denied with an audit event.
- Target user becomes expired after request, before approval —
  denied.
- Cross-branch transfer request — denied at request time.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Request + approval lock the task + pending transfer rows | PASS | `select_for_update()` + audit |
| AC-2 Only one pending transfer per task (DB-enforced) | PASS | Partial unique index |
| AC-3 Approval clears prior claim / verifies target branch membership at effective time | PASS | `resolve_transfer` |
| AC-4 Authorization checked before mutation, all transitions auditable | PASS | Audit events on every branch |
| AC-5 PostgreSQL concurrency tests cover the listed scenarios | PASS | `test_transfer_concurrency.py` |

## Risks / Follow-ups

- Product and Security have approved the state machine. Any future
  change must be reflected in `apps/tasks/TRANSFER_STATE_MACHINE.md`
  and the concurrency tests.
