# Done Log

> **Instructions:** For each upgrade, when completed, add a row here.

## Log

### C-01: Fix nested BrowserRouter (done 2026-08-28)

Unified `BrowserRouter` in `main.tsx` only. `AppShellHost` consumes the Router context.

### C-02: Fix production secrets (done 2026-08-28)

`AUDIT_HMAC_SECRET` mandatory in both compose files; CI step verifies no default secrets.

### C-03: Fix WeeklyShift IDOR (done 2026-08-28)

`validate()` in serializer rejects cross-tenant references with 403. 4 new tests.

### C-04: Fix CSRF Token (done 2026-08-28)

Frontend client reads `csrftoken` cookie and sets `X-CSRFToken` on every unsafe request. `ensureCsrfToken()` pre-flights. `BootstrapView` uses `@ensure_csrf_cookie`.

### C-06: Owner Signature workflow (done 2026-08-28)

`ExitDecision` model with HMAC signature, API at `/api/v1/platform/exit-decisions/<phase>`, audit event `EXIT_DECISION_SIGNED`. 4 new tests.

### C-07: Evidence Branch IDOR (done 2026-08-28)

`context.require_branch(...)` added to every evidence, issue, message, and media view. Cross-branch references return 403.

### C-08: Membership Expiry (done 2026-08-28)

Centralised `active_membership_q()` predicate. `tenant_context` honours `active_until`. Disabled users rejected even with valid session. 3 new tests.

### C-11: Scheduler Integrity (done 2026-08-28)

Beat schedule covers scheduler, overdue, capture-session cleanup, exports, backups, lifecycle, and notifications.

### C-13: Face Privacy Enforcement (done 2026-08-28)

Server-side face detector (`_server_detect_face`) is the only authority. Client flag is informational. `privacy_decision` recorded in audit metadata. New columns: `privacy_decision`, `face_detector_version`, `face_detector_confidence`, `face_detector_raw_score`, `privacy_metadata`.

### C-14: Auth Bootstrap Trust (done 2026-08-28)

`/login` is a public route with `LoginPage`. Workspace is mounted under the authenticated tree.

### H-01: ReviewDecisionCreateView RBAC (done 2026-08-28)

`required_roles = (OWNER, MONITOR)`. 3 tests.

### H-02: ReviewPolicyView RBAC (done 2026-08-28)

`required_roles = (OWNER,)`. 4 tests.

### H-03: Real AI Provider (done 2026-08-28)

`OpenAIProvider` with allowlist, strict timeout, JSON response format, structured-output re-validation. `build_provider` selects by name. 5 tests.

### H-04: Linux Docker connector (done 2026-08-28)

FastAPI connector in `connector/`. HMAC signature, replay guard, timeout, structured logs. Dockerfile runs as non-root. 6 tests.

### H-05: Backup Encryption (done 2026-08-28)

Fernet encryption of backup artefacts. `BACKUP_ENCRYPTION_KEY` is mandatory. On-disk SHA-256 of encrypted bytes. Round-trip tests.

### H-06: PostgreSQL Restore (done 2026-08-28)

`_restore_database` selects engine via `BACKUP_RESTORE_DB_ENGINE`. SQLite default; PostgreSQL optional via the same alias.

### H-07: Fix 5 pytest failures (done 2026-08-28)

Exports now allow OWNER + MONITOR with branch-scope check via `prepare_export_request`. Backups switch to `CompanyRole.OWNER`. Transfers enforce tenant isolation in the service layer.

### H-08: Fix race in Audit chain (done 2026-08-28)

`AuditEvent.save()` now opens `transaction.atomic()` and takes a PostgreSQL advisory lock. Race test asserts no duplicate `previous_hash`.

### BE-01: RBAC Audit (done 2026-08-28)

All `TenantAPIView` subclasses declare `required_roles`. Verified by
`scripts/audit_required_roles.py --strict` AST scan (40 views added).

### BE-02: Cross-tenant reference helper (done 2026-08-28)

`validate_company_reference` / `validate_company_reference_or_none` in
`apps/tenancy/access.py`. Applied to capture-session, issue-create,
discussion-message, AI analysis, backup restore, review decision,
task claim/start/complete/cancel/transfers, and evidence-task views.
5 unit tests.

### BE-03: Tenant isolation suite (done 2026-08-28)

`tests/test_tenant_isolation.py` covers tenancy context, task
templates/instances, evidence issues, review decisions, branch
membership, backup restore. 10 cases pass.

### BE-04: Audit chain hardening (done 2026-08-28)

Checklist verified: `select_for_update` inside transaction, advisory
lock, deterministic chain head, `verify_audit_chain` checks every
link, `update`/`delete` are rejected. New
`apps/audit/tests/test_audit_chain_hardening.py` (7 cases) pins the
contract.

### BE-05: Login Failed Audit (done 2026-08-28)

`CompanyCodeBackend` records `LOGIN_FAILED` for every failure reason. Audit metadata captures `company_code`, `reason`, `remote_addr`. 7 new tests in `test_login_failure_logging.py`.

### BE-06: MFA enforcement (done 2026-08-28)

`MFAEnforcementMiddleware` blocks unverified Admin/Owner users. New
`apps/identity/mfa.py` helpers, `MFA_ENFORCEMENT_ENABLED` setting
(default off in tests). 7 new tests in `test_mfa_enforcement.py`.

### INFRA-01: Hardened Production Compose (done 2026-08-28)

`x-backend-defaults` anchor in `compose.yml` carries the hardening
baseline (user 1000:1000, `cap_drop: [ALL]`, `cap_add: [NET_BIND_SERVICE]`,
`no-new-privileges`, `pids_limit: 100`, `mem_limit: 512m`, JSON log
driver). `compose.prod.yml` redeclares the anchor and layers
`read_only: true` + tmpfs on api/worker/beat/db/redis. `compose.dev.yml`
keeps `read_only: false` so the runserver and Vite dev server can write
to the bind-mount. 9/9 base + 7/7 prod invariant assertions pass.

### INFRA-02: CSP Headers (done 2026-08-28)

`Content-Security-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy` added to nginx security headers. A strict static policy (`script-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'`) is enforced from day one because the Vite SPA bundle has no inline scripts. A parallel `Content-Security-Policy-Report-Only` header is emitted to the `CSP_REPORT_URI` collector so future inline-injection regressions are caught by the collector instead of breaking users. Headers duplicated in `infra/nginx/security-headers.conf` and `frontend/nginx.conf`.

### INFRA-03: Backup to S3 (Envelope Encryption + Key Rotation) (done 2026-08-28)

New `apps/backups/external_storage.py` implements AES-GCM envelope encryption under a per-rotation KEK. The envelope format is `mhami-external-backup-v1` (12-byte nonce || wrapped data key || payload nonce || ciphertext+tag). The data key is wrapped by a 256-bit KEK identified by `BACKUP_EXTERNAL_KEY_ID`; multiple KEKs are loaded from `BACKUP_EXTERNAL_KEYS` (JSON map) so rotation does not require decrypting existing artefacts. The `boto3` upload path is least-privilege, sets `ServerSideEncryption`, and records the SHA-256 + key_id in object metadata. `apps/backups/tasks.py` exposes `run_external_upload` as a Celery task chained after `run_backup_run`. Smoke test confirms roundtrip, key rotation, tamper detection, and wrong-key rejection.

### INFRA-04: Monitoring (done 2026-08-28)

`infra/monitoring/prometheus.yml` scrapes the platform `/api/metrics` with the bearer token. `docker-compose.override.yml` brings up Prometheus + Grafana + Alertmanager.

`infra/monitoring/compose.monitoring.yml` (new) brings up Prometheus + Alertmanager + Grafana + blackbox-exporter under `--profile monitoring`. Alert rules split per concern (`prometheus/alerts/{api,database,celery,backups}.yml`); 3 Grafana dashboards auto-provisioned (`api.json`, `database.json`, `business.json`). Alertmanager routes by severity: `critical` -> PagerDuty, `warning` -> Slack. Every monitoring container is hardened (cap_drop ALL, no-new-privileges, mem_limit, pids_limit). All images pinned to known versions.

### INFRA-05: Let's Encrypt (done 2026-08-28)

`compose.prod.yml` adds a `certbot` service (webroot issuance) and a `certbot-renew` sidecar (24h renew loop), both under `--profile certbot`. `certs` and `certbot-webroot` volumes are declared; frontend mounts them so the existing 443 server block can serve the issued certificate. ACME webroot served from `/.well-known/acme-challenge/` to keep the HTTP->HTTPS redirect intact. `LETSENCRYPT_EMAIL` and `LETSENCRYPT_DOMAIN` are required for the profile to come up. Frontend service gains a `wget --spider` healthcheck so renewals do not fire before NGINX is up.

### FE-01: Router Architecture (done 2026-08-28 — alongside C-01)

Single `<BrowserRouter>` with `/login` separated from the workspace tree.

### FE-02: Bilingual i18n (done 2026-08-28)

`react-i18next` wired up in `src/i18n/index.ts` with `en` and `ar` resources and `localStorage` persistence.

### FE-06: Playwright E2E (done 2026-08-28)

`playwright.config.ts` with local dev server. `tests/e2e/auth.spec.ts` covers landing and login routes.

---

## Statistics

| Indicator | Value | Date |
|---|---|---|
| Total upgrades | 50+ | 2026-08-28 |
| Completed this pass | 28 (5 added: INFRA-01, INFRA-03, INFRA-05, plus INFRA-02/04 expanded) | 2026-08-28 |
| INFRA scaffolds (planning + verification + goal + implementation + testing + results) | 5 (INFRA-01..INFRA-05) | 2026-08-28 |
| Critical fixes remaining | 0 (out of 14) | 2026-08-28 |
| High fixes remaining | 0 (out of 8) | 2026-08-28 |
| Backend hardening remaining | 0 (out of 6) | 2026-08-28 |  |
| Infra remaining | 0 (out of 5) | 2026-08-28 |
| QA remaining | 4 (QA-01, QA-02, QA-04, QA-05) | 2026-08-28 |
| Legal remaining | 6 (LEGAL-01..06) | 2026-08-28 |
| Pilot remaining | 6 (PILOT-01..06) | 2026-08-28 |
| Doc remaining | 5 (DOC-01..05) | 2026-08-28 |
| Phase13 remaining | 4 (PHASE13-01..04) | 2026-08-28 |
| Frontend rebuild remaining | 2 (FE-03 OpenAPI gen, FE-04 Workflow binding) | 2026-08-28 |

---

## Lessons Learned

### Sprint 2 (this pass)

- **BE-02 helper** (`validate_company_reference`) is the single source
  of truth for cross-tenant reference validation. Future serializers
  must call it instead of inlining `.get(..., company=company)`.
- **C-13** privacy decision is now recorded as a first-class field.
  Future reviews must treat the client `face_detected` flag as
  informational only.
- **H-04** connector uses HMAC + replay guard + freshness window. The
  pattern is reusable: the platform can issue the same signed
  envelope for outbound connector jobs in a future release.
- **H-08** advisory lock is the right primitive for serialising the
  audit chain. The advisory key (`0x4D48414D49`) is reserved for the
  audit subsystem.
- **INFRA-04** Prometheus + Grafana + Alertmanager bring-up is
  described in `infra/monitoring/docker-compose.override.yml`. The
  metrics token is stored as a Docker secret and never logged.

### INFRA scaffolding (2026-08-28)

- 5 packages × 6 files = **30 files** added under
  `upgrads/05_INFRASTRUCTURE/`:
  - `INFRA-01_HARDENED_COMPOSE/` — anchor parity + cap_drop/read_only on every service
  - `INFRA-02_CONTENT_SECURITY_POLICY/` — Report-Only → Enforced, with `csp-report` view + Playwright spec
  - `INFRA-03_BACKUP_S3_UPLOAD/` — envelope encryption + retry + checksum + weekly drill
  - `INFRA-04_PROMETHEUS_GRAFANA/` — 4 exporters + alert rules + dashboards + Alertmanager + 5 runbooks
  - `INFRA-05_LETS_ENCRYPT/` — `bootstrap-cert` + `certbot-renew` + nginx :80/:443 + HTTPS smoke CI + `CertExpiringSoon` alert
- Each package contains `00_DISCOVERY`, `01_VERIFICATION`, `02_GOAL`,
  `03_IMPLEMENTATION`, `04_TESTING`, `04_RESULTS`.
- These planning packages are reference material; the live implementation
  status is captured above in the FE-02/FE-06/INFRA-* "done 2026-08-28"
  notes.
