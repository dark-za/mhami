# Backup Assets

Backup and recovery guidance for the platform.

The authoritative backup/restore procedures live under
`../docs/BACKUP_RESTORE.md` and `../docs/runbooks/restore.md` (application
rollback vs. migration recovery is distinguished in `../docs/runbooks/rollback.md`
and `../docs/runbooks/deployment.md`).

Backup/restore status is observable via the API system-status endpoint
(`GET /api/v1/status`, `metrics.backups.*`).

## Validation limits

No backup automation exists in this environment, and there is no second backup
destination wired. Restore proof against a production-equivalent topology is
required before the first external tenant is admitted (Phase 13). Restore and
incident runbooks must be validated in staging, not here.