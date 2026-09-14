# Rollback Runbook

Return the service to the last known-good release artifact after a failed deployment or regression.

## Steps

1. Pause administrative changes and task scheduling while rolling back.
2. Redeploy the previous immutable artifact (previous Git SHA / version) using `compose.prod.yml`.
3. Do **not** silently reverse database migrations. If the failed release added a non-commutative migration, follow the documented forward-only migration policy; an in-place downgrade is only allowed where the migration is explicitly reversible.
4. Restore application state from the last good backup if data integrity is at risk (see `restore.md`).
5. Verify readiness endpoints and security headers return to normal.
6. Record the incident in the organization’s incident report and release log.

## Success criteria

- Healthy API and frontend on the previous artifact.
- No organization data loss; audit log retains the deployment and rollback events.
