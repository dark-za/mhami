# Changelog

## Unreleased

### Frontend Reliability

- Report successful People, MCP access, task, and review changes even when the
  follow-up refresh fails, with explicit stale-data warnings to prevent duplicate
  submissions and preserve one-time MCP secrets.
- Create scheduled tasks through a single backend endpoint so the task template,
  first version, and schedule are persisted atomically.

### Test Reliability

- Force backend pytest runs onto `config.settings.test` and isolate auth throttle
  cache state in tenancy API tests.

### Documentation and Policy

- Simplify legal policy documents for the self-hosted single-organization
  release. The seed command now publishes six operator-facing notices and omits
  the old remote-assistance/support authorization document.

### Container Reliability

- Include frontend validation scripts in Docker builds; CI also builds the
  production frontend image.
- Bind development ports to loopback and wait for API health during Compose
  startup. Add resolved Compose contract tests for development/production.

### Authentication Corrections

- Disabled users are rejected during login and are no longer restored from sessions.
- Owner-created accounts no longer submit hidden branch/job-role fields;
  monitor-created employees retain their required scoped assignment fields.
- Login, first-owner setup, and member creation preserve passwords exactly,
  including surrounding whitespace, consistently with `provision_owner`.
- Compatibility: passwords previously created through the API had surrounding
  whitespace removed before hashing. Those existing hashes are unchanged; use
  the previously stored password without the removed whitespace. No automatic
  password rewrite or alternate trimmed-password login is performed.

- Phase 01 governance and repository foundation documents added.

### Backend Hardening (Section 4)

- **BE-01** — Every `TenantAPIView` subclass now declares an explicit
  `required_roles` tuple. A new static-audit script
  `backend/scripts/audit_required_roles.py` walks the `apps/` tree and
  fails the build (`--strict`) when a view is missing the contract.
  CI is wired through this script.
- **BE-02** — Added `validate_company_reference` /
  `validate_company_reference_or_none` helpers in
  `apps/tenancy/access.py`. Applied them to the high-risk endpoints
  (capture session, issue create, discussion message, AI analysis,
  backup restore, review decision) so cross-tenant ID probes are
  turned into 403s instead of leaking existence.
- **BE-03** — New `tests/test_tenant_isolation.py` suite pins the
  cross-tenant boundaries for tenancy context, task instances,
  evidence, review decisions, branch membership, and backup restore.
- **BE-04** — Hardening checklist verified: audit chain uses
  `select_for_update` plus a PG advisory lock, `previous_hash` is
  derived from chain head, `verify_audit_chain` checks every link,
  and `AuditEvent.delete/update` are rejected. New
  `apps/audit/tests/test_audit_chain_hardening.py` locks the
  contract.
- **BE-05** — Failed login attempts are recorded in the audit chain
  by `CompanyCodeBackend` with reason codes (`missing_fields`,
  `unknown_company`, `inactive_company`, `unknown_user`,
  `bad_password`, `not_authorized_for_company`,
  `missing_mfa_enrollment`). New
  `apps/tenancy/tests/test_login_failure_logging.py` exercises every
  reason.
- **BE-06** — `apps/identity/middleware.py::MFAEnforcementMiddleware`
  blocks Platform Admin / company Owner users that have not verified
  a TOTP enrollment. The middleware is wired into
  `MIDDLEWARE` and is gated by the new
  `MFA_ENFORCEMENT_ENABLED` setting (disabled in tests by default).
  `apps/identity/mfa.py` exposes the helpers used by the middleware
  and the login view.
