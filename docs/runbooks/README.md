# Runbooks

Operational runbooks are written during Phase 11 and must be exercised before production launch.

Available runbooks:

- `PILOT_OPERATIONS.md` — setup and operation of the Phase 12 internal pilot.
- `deployment.md` — promotion of a validated release candidate to production.
- `rollback.md` — return to the last-known-good release.
- `restore.md` — backup restore procedure.
- `incident-response.md` — media, AI/connector, backup, tenant, and security incident response.
- `support-authorization.md` — grant and revoke temporary tenant support access.

Required remaining runbooks include media storage capacity growth, AI auto-pass gating, and tenant export/read-only exercise.

## Celery beat tasks

Scheduled tasks live in `CELERY_BEAT_SCHEDULE` in `backend/config/settings/base.py`:

| Beat entry | Task | Schedule |
| --- | --- | --- |
| `process-lifecycle-expirations-daily` | `apps.tenancy.process_lifecycle_expirations` | Daily 02:00 UTC |
| `create-daily-backups` | `apps.backups.create_daily_backups` | Daily 02:30 UTC |
| `cleanup-expired-exports-hourly` | `apps.exports.cleanup_expired_exports` | Hourly |
| `process-notification-outbox` | `apps.notifications.process_outbox_events` | Every 5 minutes |

The lifecycle, backup, export-cleanup, and notification-outbox tasks are idempotent and safe to rerun. They require a Celery worker and beat scheduler; the development compose stack does not start one by default.

## Asynchronous exports and backups

Export artifact generation (`apps.exports.tasks.enqueue_export_request`) and backup creation (`apps.backups.tasks.enqueue_backup_run`) are exposed as Celery tasks with a synchronous fallback. The API views call the `enqueue_*` helpers, which probe for a reachable Celery worker (`apps.platform_core.services.broker_available`) and:

- dispatch the heavy work to the worker when one responds, returning a `queued`/`requested` row immediately, or
- fall back to running the existing services inline when no broker or worker is reachable, so the public API response contract is unchanged.

The development stack runs Redis but no Celery worker, so exports and backups execute synchronously until a worker is added. Outbox events recorded by `backup.completed`, `backup.restore.completed`, and `exports.completed` are consumed by `apps.notifications` (directly at the event site and by the notification-outbox beat task) and produce in-app notifications.