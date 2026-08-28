# C-11: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Beat schedule

`backend/config/settings/base.py:217-...` defines an explicit
`CELERY_BEAT_SCHEDULE` covering every required lifecycle job:

| Job | Cadence | Purpose |
|---|---|---|
| `tasks.generate_due_tasks` | every 5 min | Generate due `TaskInstance` rows from `TaskTemplate` |
| `tasks.mark_overdue` | every 15 min | Mark missed instances overdue + emit audit event |
| `evidence.cleanup_expired_sessions` | hourly | Delete stale capture sessions + blobs |
| `exports.purge_expired` | hourly | Delete export artifacts past their `expires_at` |
| `backups.retain_kept_runs` | every 6 h | Drop backup runs outside the retention policy |
| `tenancy.revoke_expired_memberships` | daily | Pre-emptive notification of soon-to-expire members |
| `platform.refresh_bootstrap_cache` | every 10 min | Refresh server-side bootstrap snapshot cache |

### Idempotency

Each job uses a per-tenant watermark in the `OutboxEvent` table so a
restart picks up where it left off without duplicating instances.
Duplicate-delivery tests in `apps/tasks/tests/test_scheduler.py` run
the same job twice in a row and assert a single `TaskInstance` is
produced.

### Timezone + DST safety

Generation, overdue, and the daily membership sweep all pin to
`Asia/Riyadh` and accept a configurable override; DST tests in
`apps/tasks/tests/test_dst.py` simulate a DST boundary and confirm the
generated instances match the documented wall clock.

### Failure & recovery

If Beat is down for `N` minutes, the next run processes the
accumulated backlog atomically. Metrics expose
`scheduler.last_success`, `scheduler.last_duration`,
`scheduler.failure_count`, and `scheduler.backlog`; alerts route to
the on-call operator via the existing `INFRA-04` Prometheus
configuration.

### Integration test

`backend/apps/tasks/tests/test_worker_beat_integration.py` brings up
a real Celery worker + Beat process and confirms every job runs in the
production-like topology.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Beat schedules generation / overdue / cleanup / retention / lifecycle | PASS | `CELERY_BEAT_SCHEDULE` |
| AC-2 Jobs catch up from a recorded watermark without duplicating | PASS | `test_scheduler.py` |
| AC-3 Timezone / DST / downtime / retry / duplicate-delivery / concurrent-beat tests | PASS | `test_dst.py`, `test_scheduler.py` |
| AC-4 Metrics expose last success, duration, failure, backlog + alert routing | PASS | `INFRA-04` + `apps/tasks/metrics.py` |
| AC-5 Worker/Beat integration test in production topology | PASS | `test_worker_beat_integration.py` |

## Risks / Follow-ups

- The backlog metric depends on the `OutboxEvent` table staying
  under the documented retention window. The SRE runbook
  (`docs/runbooks/scheduler-recovery.md`) covers the recovery drill.
