# Incident Response Runbook

Standard response for production incidents. Applies to media storage failure, AI/connector failure, tenant suspension, tenant deletion, and security incidents, each with its own checklist below.

## Common flow

1. **Detect**: alert rule fires (see `infra/monitoring/alert-rules.yml`) or a user reports an issue.
2. **Triage**: confirm severity and tenant impact; assign an owner.
3. **Mitigate**: apply the relevant containment steps; do not bypass audit.
4. **Restore**: return service and data to a known-good state (see `restore.md`).
5. **Review**: document root cause, corrective actions, and approval in the incident report; update the runbook if the procedure was wrong.

## Media storage failure

- Trigger: evidence uploads fail or face-blur derivatives cannot be written.
- Mitigate: verify `MEDIA_ROOT` writability and media volume (`media-data:/app/media` in `compose.prod.yml`); free space or add capacity.
- Impact: evidence submission must still complete without data loss; use the queue/retry path. Do not allow gallery-upload fallback in the pilot.

## AI or connector failure

- Trigger: `ConnectorOffline` alert or AI transfer fails.
- Mitigate: confirm AI stays in Shadow Mode; evidence submission must continue without AI decision. Verify connector enrollment health and restart the connector if needed.

## Backup failure

- Trigger: `BackupExpired` alert.
- Mitigate: confirm backup destination reachable, rerun the scheduled backup, and validate with a restore test (`restore.md`).

## Tenant suspension / deletion

- Suspend: move the company to `SUSPENDED`, block logins and onboarding, retain data per retention policy.
- Delete: follow the documented deletion flow; run the 90-day read-only path with safe fixtures first; preserve audit evidence.

## Security incident

- Contain: revoke access, revoke leaked secrets (`docs/SECRET_MANAGEMENT.md`), and preserve audit logs.
- Investigate: reconstruct from audit events and backups.
- Notify: reach affected tenant owner and the Platform Administrator, per the alert routing matrix.