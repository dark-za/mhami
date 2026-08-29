# Public Release Plan

## Purpose

This plan defines the release path for preparing Mhami for public source distribution and later production operation. Public source readiness and production readiness are separate gates.

## Gate 1: Repository Hygiene

Required before making the repository public:

- Remove internal execution logs, stale audit reports, and contradictory delivery dashboards.
- Keep only documentation that helps users install, understand, operate, or contribute to the project.
- Ensure no `.env`, database files, private keys, local archives, generated caches, or local machine paths are tracked.
- Keep legal placeholders clearly labeled until counsel approval exists.
- Keep CI passing on the default branch.

## Gate 2: Developer Experience

Required before inviting external developers:

- Provide a truthful root README with local and production setup.
- Keep backend, frontend, connector, and infrastructure READMEs aligned with the actual code.
- Provide a license and security reporting policy.
- Document common quality commands.
- Publish a concise roadmap with completed, current, and blocked work.

## Gate 3: Technical Hardening

Required before pilot or production use:

- Confirm tenant isolation, branch scoping, review RBAC, evidence privacy, and transfer invariants with tests.
- Keep production settings fail-fast for all required secrets.
- Ensure AI analysis uses the configured provider boundary and remains in shadow mode unless an explicit approved gate enables automation.
- Verify encrypted backup, external upload, and restore workflows in a production-equivalent environment.
- Run dependency, container, secret, and SAST scans.

## Gate 4: Operational Readiness

Required before production launch:

- Complete deployment, rollback, restore, monitoring, incident-response, and support runbooks.
- Run a production-equivalent restore drill.
- Define support rota, escalation matrix, and release communication process.
- Record owner approvals for launch, rollback authority, and exception handling.

## Gate 5: Legal And Pilot Readiness

Required before real customer or employee data:

- Obtain qualified legal review for terms, privacy, employee privacy, AI transfer, retention, support access, ROPA, DPIA, and breach response.
- Replace placeholder legal text with approved versions.
- Run a real authorized pilot and record weekly reports from actual operations.
- Link owner sign-offs to auditable system records.

## Current Status

- Repository hygiene: in progress.
- Developer experience: in progress.
- Technical hardening: partially complete, CI-backed for the default branch.
- Operational readiness: incomplete until production-equivalent drills and support rota exist.
- Legal and pilot readiness: incomplete; legal documents and pilot evidence remain placeholders until authorized review and real pilot data are recorded.
