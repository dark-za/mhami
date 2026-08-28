# Phase 3: Production Readiness and Controlled Launch

## Assigned Agent

`LAUNCH-GATE-03`

## Objective

Execute Phase 13 only after approved Phase 12 exit evidence exists. Produce a stable, supportable, reversible controlled external launch without bypassing the staging, security, recovery, or legal gates.

## Required Inputs

- Approved handoff and go decision from `PILOT-ASSURANCE-02`.
- Phase 13 gate document: `docs/phases/13_PRODUCTION_READINESS_AND_CONTROLLED_LAUNCH.md`.
- Production topology and runbooks:
  - `compose.prod.yml`
  - `frontend/nginx.conf`
  - `infra/nginx/security-headers.conf`
  - `infra/monitoring/alert-rules.yml`
  - `docs/runbooks/deployment.md`
  - `docs/runbooks/rollback.md`
  - `docs/runbooks/incident-response.md`
  - `docs/runbooks/restore.md`
  - `docs/runbooks/support-authorization.md`
- Current Phase 11 security, restore, and release-risk evidence.

## Scope

1. Freeze release scope except approved defect fixes.
2. Build immutable release artifacts that record version, Git SHA, build time, and schema version.
3. Run the complete CI and security gate set on the release candidate:
   - Backend lint, type checks, tests, migration safety, OpenAPI validation, and dependency audit.
   - Frontend typecheck, tests, build, and dependency audit.
   - Container, secret, and image-supply-chain scans when the production CI integration is available.
4. Deploy the unchanged release candidate to staging, rehearse migration and rollback, and record evidence.
5. Prepare production infrastructure:
   - Real TLS certificates mounted for NGINX.
   - Cloudflare Tunnel configuration and external DNS.
   - Production secrets stored outside Git and restricted per service.
   - Backup destination, retention, encryption, and restore exercise.
   - Monitoring probes and alert routing tested to accountable recipients.
6. Verify production smoke tests: HTTPS, HTTP-to-HTTPS redirect, NGINX API proxy, security headers, API health, media write path, database, Redis, worker queues, connector, and AI Shadow Mode.
7. Start controlled external onboarding in small cohorts only after all gates pass; monitor and pause automatically on a stop condition.

## Explicit Exclusions

- Do not deploy directly from development to production.
- Do not use placeholder certificates, test credentials, or dummy backup destinations in production.
- Do not enable self-service registration before abuse controls, support, trial lifecycle, suspension, and deletion workflows are proven.
- Do not roll back a database by silently reversing irreversible migrations.
- Do not enable AI auto-pass as part of launch.

## Required Deliverables

- Release candidate sign-off containing version, Git SHA, build time, schema version, and migration plan.
- Staging deployment, migration, rollback, and restore evidence.
- Production TLS, tunnel, secret-management, backup, monitoring, and alert-routing evidence.
- Controlled-launch cohort plan, support rota, escalation matrix, and public operating-status procedure.
- Final production go/no-go decision signed by the platform owner.

## Verification Checklist

- Production uses the reviewed `compose.prod.yml` topology with non-root/read-only hardening where configured.
- HTTPS terminates correctly, port 80 redirects to HTTPS, and proxy headers prevent Django redirect loops.
- A backup exists before migration and an independent restore exercise succeeds.
- Alert routing is tested end to end; no alert rule references fabricated metrics.
- Tenant registration, trial lifecycle, suspension, deletion, exports, and support authorization are exercised safely in staging.
- Rollback and incident paths are demonstrated, not assumed.

## Exit Gate

Phase 13 is complete only when the platform owner accepts evidence that the platform is observable, recoverable, supportable, secure, and safely available beyond the internal pilot.

## Stop Conditions

- Any unresolved critical security, tenant-isolation, backup, migration, or incident-response defect.
- Missing real TLS, alert routing, or verified rollback path.
- External self-service onboarding enabled before all controlled-launch gates are satisfied.
