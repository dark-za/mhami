# C-11: Make Scheduler and Lifecycle Jobs Operable

## Discovery

Task generation, overdue marking, and capture-session cleanup exist as code but
are not all scheduled in Celery Beat:

- `backend/apps/tasks/tasks.py`
- `backend/apps/evidence/tasks.py`
- `backend/config/settings/base.py:209-226`

The scheduler also needs explicit recovery behavior after Beat downtime.

## Goal

Schedule and observe all required lifecycle jobs with deterministic recovery,
idempotency, and timezone-safe behavior.

## Acceptance Criteria

1. Beat schedules generation, overdue marking, expired-session cleanup,
   export cleanup, backup retention, and tenant lifecycle jobs explicitly.
2. Jobs catch up from a recorded watermark without duplicating task instances.
3. Timezone, DST, downtime, retry, duplicate-delivery, and concurrent-beat
   tests run against PostgreSQL/Redis.
4. Metrics expose last success, duration, failure, and backlog; alerts route to
   an accountable operator.
5. A worker/beat integration test proves jobs run in the production topology.

## Required Evidence

- Beat schedule artifact and integration-test output.
- Failure/recovery drill result.
- SRE approval.
