# Changelog

## Unreleased

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
