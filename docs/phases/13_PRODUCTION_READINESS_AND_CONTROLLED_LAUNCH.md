# Phase 13: Production Readiness and Controlled Launch

## Status

Not started. This is a planned gate document; it may not begin until Phase 12 exits and the entry requirements below are approved.

## Objective

Release a stable, supportable, and reversible SaaS platform through controlled rollout, not direct development deployment. The platform is offered beyond the internal pilot only after observability, recovery, support, and legal readiness are demonstrated and accepted by the platform owner.

## Entry Requirements

- Phase 12 exit criteria are approved (pilot success measures, resolved high-severity defects, and capacity/recovery/legal/support findings incorporated into the release candidate).
- Release scope is frozen except for defect fixes.
- Production server inventory, backup destination, credentials, Cloudflare Tunnel, monitoring, and legal-policy documents are complete.
- The Phase 11 evidence is current: `docs/PHASE11_SECURITY_REVIEW.md`, `docs/PHASE11_RESTORE_TEST_REPORT.md`, and `docs/PHASE11_RELEASE_RISK_REGISTER.md` are approved and the risks they record are accepted or mitigated.
- Production deployment artifacts exist and are reviewed: `compose.prod.yml`, `frontend/Dockerfile`, and `frontend/nginx.conf` (TLS termination, HTTP-to-HTTPS redirect, API reverse proxy) are finalized.
- `docs/BACKUP_RESTORE.md`, `docs/RUNBOOK.md`, and the procedures under `docs/runbooks/` are validated against the staging-equivalent environment.

## Scope

- Produce immutable release artifacts that carry application version, Git SHA, build time, and schema version, and that are promoted unchanged from staging to production.
- Run the full quality gate set defined in `docs/CI_QUALITY_GATES.md` and `docs/TEST_STRATEGY.md`, including dependency audit, container scan, and secret scan.
- Review each database migration for forward compatibility and rollback implications; rehearse migration and rollback in staging before production.
- Deploy through staging before production using the `compose.prod.yml` topology (db, redis, api on Gunicorn, frontend/NGINX, Celery default/media/AI workers) behind Cloudflare Tunnel; never deploy directly from development to production.
- Verify TLS is provisioned (certbot/ACME certificates mounted at `/etc/nginx/certs` as required by `frontend/nginx.conf`) and that security headers from `infra/nginx/security-headers.conf` are applied; confirm the port-80 redirect and `/api` proxy behavior.
- Enable self-service registration only after abuse controls, support procedures, trial lifecycle, and tenant-deletion jobs are validated in the pilot.
- Launch tenant onboarding in controlled cohorts and monitor operational, security, media, connector, and AI signals through the system-status and alerting paths established in Phase 11 (`infra/monitoring/alert-rules.yml`).
- Maintain incident response, support authorization, export, suspension, and deletion procedures consistent with `docs/legal/SUPPORT_ACCESS_AUTHORIZATION.md` and the `exports` module.
- Demonstrate backup and restore proof against the production-equivalent topology before the first external tenant is admitted.

## Required Software and Services

- Production Docker Compose topology in `compose.prod.yml`, Cloudflare Tunnel, NGINX (`frontend/nginx.conf` + `infra/nginx/security-headers.conf`), Gunicorn, PostgreSQL 17, Redis 8.2.x, Celery 5.6.x workers (default/media/AI queues), monitoring and alert routing (`infra/monitoring`), encrypted backup to a second destination, and release CI.
- Release CI that builds immutable images, records version/Git SHA/build time/schema version, runs scans, and promotes artifacts from staging to production.

## Security and Data Requirements

- Never deploy directly from development to production; promote immutable artifacts through staging.
- Never hot-edit containers; apply changes through reviewed releases and rollbacks.
- Secrets remain outside Git and are least-privileged by service; production access is individually attributable and protected by MFA.
- Rollback procedures distinguish application rollback from migration recovery.
- Private media authorization, tenant isolation, face-derivative handling, and audit integrity established in Phases 04/05/07 must hold under production load and external tenants.
- TLS is mandatory in production; certificates must be provisioned before relying on HTTPS, per `frontend/nginx.conf`.
- No container mounts the Docker socket; containers run non-root and read-only where practical, consistent with `compose.prod.yml` and the Phase 11 hardening baseline.

## Deliverables

- Release candidate checklist and sign-off, including version, Git SHA, build time, and schema version.
- Production deployment and rollback runbook (application rollback vs. migration recovery).
- Support and incident runbooks under `docs/runbooks/`.
- Public operating status and tenant-support process.
- Post-launch monitoring and review schedule derived from the Phase 11 system-status and alerting configuration.
- Backup restore proof and current restore procedure validated against the production-equivalent topology.
- Security sign-off referencing `docs/PHASE11_SECURITY_REVIEW.md` and `docs/SECRET_MANAGEMENT.md`.

## Verification

- Staging and production smoke tests pass, including the NGINX `/api` proxy, TLS termination, and HTTP-to-HTTPS redirect.
- Backup exists before migration and the restore procedure is current and tested, not assumed.
- System status accurately reports app, database, Redis, scheduler, media, connector, and AI states.
- A controlled new-company registration and trial lifecycle pass in production without exposing other tenant data; tenant-deletion and suspension jobs are exercised safely.
- Alert routing reaches the Platform Administrator, technical team, and affected tenant owner only where appropriate, validated against `infra/monitoring/alert-rules.yml`.
- Self-service registration remains disabled until abuse controls, support procedures, trial lifecycle, and tenant-deletion jobs are validated.

## Exit Criteria

- The platform can be safely offered beyond the internal pilot.
- Production is observable, recoverable, supportable, and governed.
- Outstanding risks are documented and accepted by the platform owner (carried from `docs/PHASE11_RELEASE_RISK_REGISTER.md`).
- Rollback and incident paths are verified end to end.

## Stop Conditions

- Any critical security, tenant-isolation, backup, or migration defect remains unresolved.
- Production release lacks a verified rollback and incident path.
- TLS is not provisioned or security headers are not applied.
- Self-service registration is enabled before abuse controls, support procedures, trial lifecycle, and tenant-deletion jobs are validated.
