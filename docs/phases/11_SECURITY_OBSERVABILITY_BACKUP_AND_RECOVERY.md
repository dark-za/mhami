# Phase 11: Security, Observability, Backup, and Recovery

## Status

Complete.

## Objective

Demonstrate that the platform can operate safely under failure, intrusion attempts, dependency outages, data-retention events, and recovery scenarios before the internal pilot begins.

## Entry Requirements

- Phase 10 is complete.
- Server inventory, backup destination, RPO/RTO target, and operational ownership are approved.
- Staging environment is available with safely representative configuration.

## Scope

- Harden production and staging container, network, secret, TLS, Cloudflare, NGINX, and security-header configuration.
- Implement health checks for application, modules, database, Redis, workers, media storage, connector control, and AI state.
- Implement metrics and alerts for disk, database, Redis, queue depth, worker health, backup status, connector health, AI error rate, and tenant lifecycle jobs.
- Implement encrypted backup of PostgreSQL, private media, protected configuration, and policy data to a second destination.
- Implement and test restore procedures.
- Implement retention cleanup for export files, temporary media, raw source images, expired sessions, suspended-tenant data, and backup expiry.
- Execute ASVS review, dependency audit, container scan, secret scan, authorization tests, file-upload abuse tests, and failure injection.

## Required Software and Services

- NGINX, Cloudflare Tunnel, Docker Compose, health check tooling, backup storage, structured logs, security scanners, and staging environment.

## Security and Data Requirements

- Database and Redis stay off public and unnecessary LAN interfaces.
- No container mounts Docker socket.
- Containers run non-root and read-only where practical.
- AI outage routes evidence to review; Redis outage preserves committed business transactions through outbox recovery.
- Media storage outage cannot falsely complete evidence.
- Backup contents are encrypted and restoration is tested, not assumed.

## Deliverables

- Security hardening configuration and review record.
- Health and system-status views.
- Monitoring and alert-routing configuration.
- `docs/BACKUP_RESTORE.md`, `docs/RUNBOOK.md`, and incident procedures under `docs/runbooks/`.
- Security test report, restore-test report, and release-risk register.

## Verification

- Restore a representative database and media backup into an isolated environment.
- Disconnect Redis, AI, media storage, and connector paths in staging and observe safe recovery.
- Verify tenant isolation, IDOR resistance, session revocation, MFA, export authorization, and connector revocation.
- Verify automatic deletion lifecycle against a non-production tenant fixture.
- Verify alerts reach the Platform Administrator, technical team, and affected tenant owner only where appropriate.

## Exit Criteria

- Daily operational recovery target is demonstrable.
- Critical security and recovery failures have documented responses.
- Staging passes the complete security, backup, and failure test suite.

## Stop Conditions

- Backups have not been restored successfully.
- A critical vulnerability remains unresolved without a documented approved exception.
- Production dependencies are publicly exposed or secrets are embedded in images.
