# Public Release Plan

## Purpose

This plan defines the release path for preparing Mhami for public source distribution and later production operation. Public source readiness and production readiness are separate gates. Mhami is a single-organization, self-hosted product per `docs/ARCHITECTURE.md`; there is no shared SaaS tenant lifecycle.

## Gate 1: Repository Hygiene

Required before making the repository public:

- Remove internal execution logs, stale audit reports, and contradictory delivery dashboards.
- Keep only documentation that helps users install, understand, operate, or contribute to the project.
- Ensure no `.env`, database files, private keys, local archives, generated caches, or local machine paths are tracked.
- Keep the simplified data-handling notices truthful: the organization operating
  the server is responsible for its accounts and data. They are not a claim of
  general legal compliance; see `docs/legal/README.md`.
- Keep CI passing on the default branch.

## Gate 2: Developer Experience

Required before inviting external developers:

- Provide a truthful root README with local and production setup (single organization via `provision_owner`, no public registration).
- Keep backend, frontend, connector, and infrastructure READMEs aligned with the actual code.
- Provide a license and security reporting policy.
- Document common quality commands.
- Publish a concise roadmap with completed, current, and blocked work.

## Gate 3: Technical Hardening

Required before production use:

- Confirm single-organization isolation, branch scoping, review RBAC, evidence privacy, and transfer invariants with tests.
- Keep production settings fail-fast for all required secrets.
- Ensure AI analysis uses the configured provider boundary and remains in shadow mode unless an explicit approved gate enables automation. External AI requires operator configuration and owner acceptance; a fake local provider is the default.
- Verify local encrypted backup and, if configured, external S3-compatible upload and restore workflows in a production-equivalent environment. External upload is optional operator infrastructure and must be verified separately.
- Run dependency, container, secret, and SAST scans.

## Gate 4: Operational Readiness

Required before production launch:

- Complete deployment, rollback, restore, monitoring, and incident-response runbooks. Runbooks under `docs/runbooks/` that reference the retired multi-tenant model are marked historical and are not operational for this edition (see `docs/runbooks/README.md`).
- Run a production-equivalent restore drill from the encrypted external copy (or from local artifacts if no external destination is configured) into an isolated target; record measured RPO/RTO.
- Define support rota, escalation matrix, and release communication process within the operating organization (no central/upstream support path exists by default).
- Record owner approvals for launch, rollback authority, and exception handling.
- Evidence a production checklist in an isolated environment: TLS termination, secrets from a secret manager, backup/restore, and monitoring/alerting all verified (see `docs/INSTALLATION.md` and `docs/ARCHITECTURE.md` Supported vs Optional).

## Gate 5: Organization Readiness

Required before real customer or employee data:

- Review the supplied data-handling notices for the organization’s own context,
  then replace or supplement them where required by applicable law.
- Record the organization owner’s launch, rollback, and operational approvals.
- Do not represent legal or regulatory compliance unless the organization has
  obtained and recorded the appropriate advice and evidence.

## Current Status

- Repository hygiene: local source, history, and secret scans are complete; CI confirmation and release review remain.
- Developer experience: local install-independent quality checks are complete; CI confirmation remains.
- Technical hardening: local authentication, authorization, upload, export, and browser checks are complete. CI security scans and production-equivalent drills remain required.
- Operational readiness: incomplete until production-equivalent drills and support rota exist.
- Organization readiness: each operator remains responsible for its own launch
  approvals and legal context. Production promotion remains blocked until the
  operator verifies the production checklist.
