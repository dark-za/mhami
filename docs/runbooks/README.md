# Runbooks

Operational runbooks describe the current self-hosted edition and must be
exercised by the organization before production launch.

Available runbooks:

- `deployment.md` — promotion of a validated release candidate to production.
- `rollback.md` — return to the last-known-good release.
- `restore.md` — backup restore procedure.
- `incident-response.md` — media, AI/connector, backup, organization, and security incident response.

No upstream support-access runbook exists: the project has no central support
account path into an installation.

## Celery beat tasks

Scheduled tasks live in `CELERY_BEAT_SCHEDULE` in `backend/config/settings/base.py`:

| Beat entry | Task | Schedule |
| --- | --- | --- |
| `create-daily-backups` | `apps.backups.create_daily_backups` | Daily 02:30 UTC |
| `cleanup-expired-exports-hourly` | `apps.exports.cleanup_expired_exports` | Hourly |
| `process-notification-outbox` | `apps.notifications.process_outbox_events` | Every 5 minutes |
| `run-scheduler-every-minute` | `apps.tasks.run_scheduler` | Every minute |
| `mark-overdue-tasks-quarter-hourly` | `apps.tasks.mark_overdue` | Every 15 minutes |
| `cleanup-expired-capture-sessions-every-5-min` | `apps.evidence.cleanup_expired_sessions` | Every 5 minutes |

The backup, export-cleanup, notification-outbox, task, and evidence cleanup
tasks are idempotent and safe to rerun. They require a Celery worker and beat
scheduler; the shared `compose.yml` starts both services alongside the API.

## Exports and backups

The current REST API completes owner-requested exports and backups synchronously,
then records their audit and outbox events. Celery owns scheduled backups, task
scheduling, cleanup, and notification delivery. The `enqueue_*` helpers remain
available for deliberate background integrations, but they are not the REST
request path. This distinction is intentional so the documented API behaviour
matches the code users run.
