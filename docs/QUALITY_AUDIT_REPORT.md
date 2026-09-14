# Mhami Quality Audit Report

Date: 2026-09-12
Status: Engineering verification updated; this report is not a production-release approval.

## Follow-up: post-mutation refresh handling (2026-09-12)

- **Medium, user-facing data integrity risk:** `PeoplePage` treated a failed
  follow-up refresh as if the write itself had failed. A user could successfully
  create a member, branch, job role, or branch assignment and then see a failure
  message if list/bootstrap refresh failed, encouraging a duplicate submission.
  Successful writes now report success, separately warn that displayed data may
  be stale, and dispatch the refreshed bootstrap only when that refresh succeeds.
- **Medium, one-time-secret usability risk:** `AgentAccessPage` created an MCP
  grant and then awaited the list refresh before showing the one-time secret. If
  the POST succeeded but the subsequent GET failed, the secret could be hidden
  even though it cannot be recovered later. The secret is now stored immediately
  after the confirmed POST, with a separate stale-data warning when refresh fails.
- The delegated tests-lane attempt for the MCP page was rejected. It produced
  invalid fixtures and assertions that did not match the frontend test harness.
  The accepted tests were rewritten and reviewed locally before being run.

The same post-write refresh pattern was then closed for `TasksPage` and
`ReviewsPage`. Task actions, transfer requests, transfer decisions, task-change
requests, task-request decisions, scheduled task creation after all writes
succeed, and review decisions now separate the confirmed write result from
follow-up refresh failures. Focused regression tests cover representative task
actions and review decisions across success, refresh failure, and write failure.

Frontend evidence for this follow-up: TypeScript checking passed, the full
Vitest suite passed **105/105** tests across **20** files, the production build
completed successfully, and the full Playwright suite passed **34/34** browser
cases. These tests mock API responses; they prove the component and browser
regression contracts, not live backend persistence.

At this point, the frontend no longer misreports a refresh failure as a write
failure. The separate partial-write risk in scheduled task creation is addressed
in the follow-up below.

## Follow-up: atomic scheduled task creation and test isolation (2026-09-12)

- **Medium, partial-write risk:** scheduled task creation in the browser called
  three endpoints in sequence: create template, create version, then create
  schedule. A failure in the later calls could leave a template/version without
  an active schedule. The backend now exposes `POST /api/v1/tasks/scheduled-tasks`
  to create the named-user template, first version, and schedule inside one
  transaction. Existing template/version/schedule endpoints remain available for
  compatibility.
- **Medium, CI reliability risk:** the full backend suite exposed auth throttle
  leakage between tenancy tests. The tenancy test module now clears the cache
  before and after each test while preserving the explicit throttle test. The
  missing-installation-state setup test now prepares the intended empty damaged
  installation state explicitly.
- OpenAPI schema and generated frontend API types were regenerated after adding
  the scheduled-task endpoint.

Verification for this follow-up: focused task API tests passed **10/10**,
tenancy API tests passed **36/36**, full backend tests passed **257/257** in the
Docker API environment, Django system checks passed, Ruff passed for the touched
backend files, mypy passed across **308** backend source files, frontend
TypeScript passed, Vitest passed **106/106**, the production frontend build
passed, and Playwright passed **34/34** browser cases.

## Follow-up: simplified self-hosted policy documents (2026-09-12)

- **Low, public-release clarity risk:** the legal workspace still carried
  historical support-access/pilot-era language that did not match the current
  self-hosted single-organization release. The published policy set is now a
  compact operator-facing set: Terms, Privacy Notice, Data Processing Terms, AI
  Transfer Notice, Employee Privacy, and Retention/Deletion.
- The old remote-support authorization document was removed from the published
  legal workspace. The seed command now publishes six simplified notices and
  keeps the deployment operator responsible for accounts, permissions, backups,
  retention, external AI provider configuration, and server operation.
- Compatibility note: the historical `support_access` enum value can still
  appear in database migrations and generated schema for existing installs.
  It is not seeded as a published policy document in the current release.

Verification for this follow-up: the legal seed command published **6**
documents in the Docker API environment, Ruff passed for the seed command,
Django system checks passed, and compliance tests passed **16/16**.

## Follow-up: container build and local startup (2026-09-11)

- **High, installation blocker:** `frontend/Dockerfile` omitted `scripts/`.
  A real Docker build failed with `MODULE_NOT_FOUND` for
  `/app/frontend/scripts/check-generated-types.mjs`, although the host build
  passed. The image now copies the scripts, and a complete `production` target
  build succeeded. CI now builds that target as well as running the host build.
  Successful image construction does not prove HTTPS deployment or certificate
  provisioning; neither was exercised in this follow-up.
- **Medium, development exposure:** the API and Vite ports were published on
  all host interfaces while Django debug was enabled. Development publishing
  now binds to `127.0.0.1`, matching the existing database/Redis bindings.
  After recreating only API/frontend containers, `compose ps` confirmed all
  four published development ports are loopback-only. Data volumes were retained.
- **Low, startup ordering:** logs showed Vite bootstrap proxy requests failing
  before the API listener started. The development frontend now depends on
  API health, not only container creation. The next `compose up` visibly waited
  for API health before starting the frontend. This ordering does not govern
  automatic Docker daemon restarts, which can still produce transient errors.

Four resolved-Compose contract tests now check development bindings, startup
ordering, internal API proxy routing, and production port isolation. The old
configuration failed the dependency condition and both API/frontend binding
assertions; all four tests pass after the fix. They use `docker compose config`
with an empty env file and validation-only required values, without launching
containers. Ruff, scoped whitespace checks, and CI YAML parsing also passed.
The new CI steps have been verified locally but have not run on GitHub yet.

The live browser reached the Arabic login page after startup. An attempted
submission used browser-autofilled credentials and received a generic HTTP 400;
it was not a valid empty-form test and does not establish the rejection's cause.
After explicitly clearing both fields, native required-field validation blocked
submission. Authenticated People/branch flows remain pending a valid owner login;
no account credentials were reset to bypass this requirement.

## Follow-up: account authentication and user creation (2026-09-11)

Three bounded corrections were independently checked:

- Disabled accounts: `LocalInstallationBackend` previously returned an inactive
  user during authentication and session restoration. It now rejects inactive
  users in both paths. Existing tenant/API checks already restricted inactive
  users; this finding is not evidence of unrestricted access to company data.
- Exact passwords: login, first-owner setup, and member creation serializers
  previously stripped surrounding whitespace. This broke login for passwords
  created verbatim by `provision_owner`. All three serializers now preserve the
  supplied password. Existing hashes are unchanged. Previously trimmed API-created
  passwords must still be entered in their stored, trimmed form; no alternate
  trimmed-password authentication or data migration was introduced.
- Owner user creation: `PeoplePage` submitted hidden `branch_id` and
  `job_role_id` fields, including empty strings rejected by UUID validation on
  a fresh installation. Owner requests now contain account fields only, leaving
  branch assignment to the existing separate form. Monitor requests still send
  the branch and job role for backend-validated, atomic scoped assignment. The
  server authorization and UUID validation rules were not relaxed.

Regression evidence: five backend tests failed before the authentication/password
fixes and passed afterward. The full local backend run completed with **253 passed,
1 skipped**, without a new coverage measurement. Local Python is 3.12, below the
project's declared 3.13 minimum, and emitted a Requests dependency-version warning.
The five new tests also passed in a disposable Compose API container using an
isolated test database. These runs did not reset the live installation database.

Frontend regression evidence: two owner payload cases failed before the fix,
while the monitor case already passed. All three passed afterward, covering
both an empty installation and preloaded branch/job-role options. The full Vitest
suite passed **76/76** tests; TypeScript checking and the production build passed.
An unsupported Testing Library query option found by TypeScript in the new test
was removed. These component tests mock API responses and do not replace a live
browser/server rehearsal or establish release-wide production readiness.

## Follow-up: setup and session lifecycle (2026-09-10)

The browser rehearsal created a test organization and owner through the UI,
then successfully logged out and logged back in. Server responses were 201,
204, and 200 respectively. The installation singleton existed before that
rehearsal, so the earlier setup rejection cannot be attributed conclusively to
a missing singleton. The missing-row recovery remains separately regression-tested.

Two observed frontend defects have now been corrected:

- Notifications were requested before authentication. Requests now require a
  live authenticated bootstrap and are scoped to company/user identity. Logout
  and identity changes abort pending requests and discard stale responses.
- Authenticated `/setup` had no route and fell through to `/`, unlike `/login`.
  Both routes now redirect owners/monitors to `/dashboard` and employees to
  `/tasks`.

Verification for this follow-up: TypeScript check, production frontend build,
and all 57 Vitest tests passed. All 33 Playwright browser tests also passed;
these use mocked API responses and do not prove live backend authorization.
New tests cover deferred notification loading,
account-switch response races, logout error cleanup, and setup redirects for
all three roles. Broader release approval remains outstanding; these checks do
not certify every backend permission, browser flow, or deployment environment.

## Scope and evidence

### Follow-up: expired sessions and multiple tabs

Successful login, setup, and logout now publish an opaque storage pulse for
other same-origin tabs. The pulse contains no credentials or account data; a
receiving tab discards its old workspace and fetches bootstrap from the server.
Storage failures do not block authentication. Returning focus to a visible tab
also revalidates in the background without unmounting a still-valid workspace.

The API wrapper requests a session recheck on HTTP 401 or the backend's explicit
403 `NOT_AUTHENTICATED` code, not on ordinary permission or CSRF denials. It does
not retry the rejected mutation. Workspace component state and selected task IDs
are scoped to the company/user identity so they do not carry into another account.

Evidence: 73 Vitest tests, TypeScript checking, scoped Ruff and whitespace checks,
and 10 Chromium authentication/session tests passed. The two-tab browser test uses
mocked server responses. Separately, two Django tests exercised the actual login,
logout, session middleware and bootstrap endpoints against an isolated test
database: expired sessions and sessions revoked from another client were denied
with `NOT_AUTHENTICATED`, with anonymous bootstrap and empty permissions. No live
installation sessions were deleted or expired for these tests. Idle on-screen
expiry without an API request or focus change is not claimed by this behavior.

### Follow-up: bootstrap ordering and anonymous state

Bootstrap updates now have a revision counter. Explicit session replacement
(including logout), hydrated login events, and newer refreshes invalidate older
requests. Superseded responses, failures, and finalizers cannot restore a previous
identity or end a newer loading state. A failed current refresh clears local
authenticated state. Anonymous responses are built from an empty default snapshot
instead of retaining the preceding user's name or company.

The default snapshot no longer contains a demonstration person's name/login or
company name/code. The shell rendering test supplies its own organization fixture.
The bootstrap client now makes one GET instead of a preliminary CSRF bootstrap
GET followed by an identical GET; that endpoint itself issues the CSRF cookie.

The free OpenCode tests lane was attempted, but timed out and left tests that
misused mocks and relied on timing. Those tests were rejected and replaced with
seven typed, deferred-promise regression cases reviewed and run independently.
All 64 Vitest tests, TypeScript checking, the frontend build, and scoped whitespace
checks passed. All nine Chromium authentication/setup tests also passed with
mocked API responses. Live server session expiry and cross-tab behavior remain separate
verification work; these tests do not establish either.

The audit used the current working tree, not only `HEAD`. It covered identity and
role boundaries, company and branch scope, tasks, evidence, reviews, AI/MCP,
backups, frontend localization and direction, Docker/CI, dependencies, generated
schema, migrations, and the public installation path. Read-only OpenCode agents
were used for security, UI, and runtime reviews; bounded agents were used only for
the backup and browser-test fixes. Agent reports were treated as leads and checked
against source and commands before acceptance.

No database reset, production data change, secret collection, commit, or push was
performed by this audit.

## Accepted findings

### High: login did not enforce CSRF before creating a session

`LoginView` disabled DRF authentication and lacked explicit CSRF protection.
The previous regression used invalid credentials and accepted either 400 or 403,
so it could pass even when authentication failed without checking CSRF.

A new test provisioned valid credentials in an isolated database. Before the fix,
three cases incorrectly returned 200: no CSRF cookie/header, a mismatched token,
and an untrusted Origin with a valid token. Explicit `csrf_protect` on the login
dispatch now rejects these with 403 before creating a session or login audit
event. Valid bootstrap cookie/header login remains successful and rotates CSRF.
The legacy test now requires exactly 403. All 34 tenancy/CSRF tests passed after
the fix, along with scoped Ruff and whitespace checks. The system Python test
environment emitted a Requests dependency-version warning; this run is not a
dependency-security audit. The session ADR documents the client contract.

### High: plaintext backup sibling was persisted on download

Before the fix, `backend/apps/backups/services.py` created a decrypted `.zip`
beside the encrypted `.enc` artifact. That left tenant data on disk after a
download and weakened the encrypted-at-rest contract.

Applied fix: `download_backup_artifact()` now returns the canonical encrypted path;
`BackupDownloadView` decrypts into an in-memory `BytesIO` response; restore keeps
its in-memory validation path. Regression tests cover readable download, absence
of a plaintext sibling, tamper rejection, encrypted restore, and monitor denial.

### High: dynamic frontend values bypassed translation

The UI audit confirmed raw API values for export status/type and connector health/
status, so Arabic mode could display English protocol values. These are assigned to
a bounded frontend implementation task; the affected surfaces now use translated
Arabic and English labels with safe protocol-value fallbacks and focused tests.

### Medium: unauthenticated screens lacked locale choice

Login and first-owner setup were Arabic-default but did not expose the existing
locale switcher. This prevents an English-only operator from choosing a language
before authentication. The bounded frontend task adds the existing control without
bringing authenticated shell navigation into public routes.

### Medium: language-switcher select used physical padding

The locale select used physical padding, which can leave the native arrow without
clearance in RTL. The bounded frontend task converts it to logical padding and adds
the narrowest useful regression coverage.

## Rejected or unverified agent claims

- Docker port exposure was incorrectly reported as a port conflict. Host-to-
  container publishing is intentional in the development override and was
  independently inspected.
- PostgreSQL/Redis tags were incorrectly classified as a critical vulnerability;
  the compose and CI values are explicit and the report supplied no compatibility
  failure.
- `python-magic` was incorrectly attributed CVE-2023-5217. The agent did not
  provide a valid package-to-CVE proof; dependency results must come from the
  package audit command.
- The timestamped `types-PyYAML` version was incorrectly called a mismatch; the
  project pins the same valid version in the relevant manifests.
- The manifest-count and test-artifact claims were not reproduced; current archive
  validation compares archive names with manifest entries and ignored test output
  is not evidence of tracked files.
- Adding Bandit/Safety as connector production dependencies is not justified by the
  runtime contract; audit tooling belongs in a CI or developer tool group.

## Independent verification recorded

The following passed before the final bounded frontend task was dispatched:

- `ruff check .`
- `mypy .` after the Pillow RGB annotation correction
- Django system checks
- `makemigrations --check --dry-run`
- OpenAPI schema validation with `spectacular --validate`
- frontend `npm audit --audit-level=high`: zero reported vulnerabilities
- initial Playwright run: 19 passed, 3 failed; failures were stale English
  assumptions and missing backend request stubs, not proven product failures
- backup-focused delegated tests: 11 passed in the agent's isolated run

The full backend coverage run and the post-fix frontend gates are recorded below.
A green frontend suite alone does not prove backend persistence or production
deployment readiness.

The full backend suite subsequently completed with **239 passed, 1 skipped**, and
**83.25% coverage** against a 70% gate. `mypy` reports no issues across 308 source
files, and `git diff --check` reports no whitespace errors.

The connector's isolated test environment also completed with **6 passed**. The
container was disposable and mounted the connector read-only; no project data was
changed by that check.

An isolated self-hosted installation rehearsal also passed: a fresh Compose
project applied all migrations, provisioned exactly one owner, then restarted
the API. The post-restart check confirmed one organization, the owner account,
valid password authentication, and a configured installation state. The audit
project and its temporary database/Redis volumes were removed afterward; the
active development volumes were not touched.

### Updated dependency evidence

The frontend lockfile was updated with the available fixes for
`@redocly/openapi-core`, `js-yaml`, and the Vitest mocker advisory. The current
full `npm audit --audit-level=moderate` reports zero vulnerabilities, and the
production-only audit is also clean.

The rebuilt frontend typecheck initially exposed a compile error in the newly added
`ExportsPage.test.tsx`; the assertion was corrected to use Testing Library queries.
The corrected focused frontend tests pass, and the production build and typecheck
also pass.

The corrected focused frontend tests now pass: AI connector and export
localization, 7/7 tests. The production build and typecheck also succeed after
generated-type verification. The development image now uses Debian slim with
Playwright Chromium and system dependencies installed at build time; the compose
development override provides writable npm/font caches and an adequate process
limit for the unprivileged test user. The complete Playwright suite then passed
**33/33** cases, covering authentication/setup, locale direction and persistence,
navigation, mobile layout, RBAC, reviews, tasks, and evidence. Production Compose
validation also passes with required metrics and audit secrets, optional external
backup settings, the corrected `/app/media` volume, and a shared named Certbot path.

## Remaining release gates

1. Review and accept/reject the bounded frontend diff; typecheck, build, Vitest,
   and the full Playwright suite are now green.
2. Backend and connector tests are green. `pip-audit -r requirements.txt`
   reports **No known vulnerabilities found**, and the full frontend audit is
   clean after the Vitest upgrade.
3. Completed: `git diff --check`, generated schema/type consistency, Compose
   validation, CI workflow checks, and the public README/installation path are
   green in the current working tree.
4. Run a staging-equivalent HTTPS deployment with real certificates and verify
   backup/restore and external integrations using operator-owned infrastructure.

## Decision

The repository is materially stronger and has one confirmed backup confidentiality
defect fixed. The application and connector test gates are reproducibly green,
including the full browser suite, and the clean-install persistence rehearsal
passed. This still does not justify claims of zero vulnerabilities or production
readiness until staging HTTPS, backup/restore, operator-owned integrations, and
the documented development-tool advisory are explicitly accepted.
