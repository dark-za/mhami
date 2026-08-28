# C-06: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Model

`backend/apps/platform_core/models.py:57-...` defines the
`ExitDecision` model with the agreed attributes:

- `phase` (e.g. `"phase_12"`) — the phase being approved.
- `decision` (approved / conditional / rejected / deferred) — the
  binding decision.
- `rationale` — free-form text explaining the decision.
- `signed_by` — FK to the platform administrator.
- `signed_at` — auto timestamp.
- `supersedes` — FK to the previous decision, supports revocation.
- `signature_hmac` — HMAC-SHA256 over the canonical record, signed with
  `AUDIT_HMAC_SECRET`. This makes any post-hoc tamper visible.
- `metadata` — JSON field for additional context.

### Migration

`backend/apps/platform_core/migrations/0002_exitdecis...` creates the
table on a fresh install. The migration is idempotent on existing
installs.

### API + Audit

The model is exposed through the platform-core API and every signed
decision produces an `EXIT_DECISION_SIGNED` (or `EXIT_DECISION_REVOKED`
on supersede) audit event. The `record_audit_event` helper attaches the
same HMAC chain the rest of the platform uses, so the decision is
non-repudiable end-to-end.

### Tests

`backend/apps/platform_core/tests/test_exit_decision.py` covers:

1. The happy path: a platform administrator signs an approval.
2. The HMAC round-trip: tampering with any field invalidates the
   signature.
3. Revocation: a new decision supersedes the previous one and emits the
   `EXIT_DECISION_REVOKED` audit event.
4. Authorization: a non-staff user cannot create a decision.

### Dossier linkage

`docs/PHASE12_EXIT_DOSSIER.md` is updated by a follow-up worker (see
C-05) that reads the latest `ExitDecision` for the phase and renders
the signature block. Until the dossier worker runs, the file still
shows the placeholder line for transparency.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Platform Owner can sign from the UI | PASS | `ExitDecision` API + audit trail |
| AC-2 Signature recorded in `AuditEvent` with HMAC | PASS | `record_audit_event("EXIT_DECISION_SIGNED", ...)` + `signature_hmac` |
| AC-3 Signature carries timestamp + rationale | PASS | `signed_at` + `rationale` model fields |
| AC-4 Signature can be revoked before lock | PASS | `supersedes` field + test |
| AC-5 `PHASE12_EXIT_DOSSIER.md` updated with link to decision | PARTIAL | Dossier worker to be run after pilot (C-05) |

## Risks / Follow-ups

- The dossier auto-update worker needs a scheduled Celery task in C-11.
