# QA-03: Goal and Plan

## SMART Goal

> Within **2 weeks (10 working days)**, install Playwright in the frontend,
> configure it against the existing `compose.dev.yml` backend, and ship
> **≥30 E2E tests** that exercise the critical user flows (login,
> navigation, evidence, reviews, RBAC, locale, CSRF, logout) — all green
> in CI as a gating job.

## Detailed Acceptance Standards

### Standard 1: Configuration

`frontend/playwright.config.ts` must:

- Set `testDir: './tests/e2e'`.
- Use the `chromium` project only (no Firefox/Safari for now).
- Boot `npm run dev` via `webServer` and reuse an existing instance locally.
- Set `trace: 'on-first-retry'` and `video: 'retain-on-failure'`.
- Use a real backend at `http://localhost:8000` (configurable via `API_URL`).

### Standard 2: Auth helper

`frontend/tests/e2e/_helpers/auth.ts` must expose a single function:

```ts
export async function login(page: Page, role: "owner" | "manager" | "supervisor" | "employee"): Promise<void>;
```

which fills the login form, submits, and waits for the dashboard URL.

### Standard 3: Spec file matrix

| File | Tests | Coverage |
|---|---|---|
| `01_auth.spec.ts` | 5 | success, wrong password, locked account, CSRF present, logout |
| `02_navigation.spec.ts` | 7 | tasks, evidence, people, reviews, admin, operations, dashboard |
| `03_evidence.spec.ts` | 6 | upload happy, size limit, signature mismatch, missing CSRF, list page, detail page |
| `04_reviews.spec.ts` | 5 | open decision, approve, reject, comment, history |
| `05_roles.spec.ts` | 5 | owner can admin, employee blocked from admin, manager limited to branch, supervisor read-only, outsider redirected |
| `06_locale.spec.ts` | 4 | EN→LTR, AR→RTL, calendar hijri persists, calendar gregorian persists |
| **Total** | **≥30** | |

### Standard 4: CI gating

`.github/workflows/ci.yml` must have an `e2e` job that:

1. Boots `compose.dev.yml` (`docker compose up -d`).
2. Waits for the backend to respond (`/api/v1/tenancy/health/`).
3. Runs `npx playwright test --reporter=line`.
4. Uploads `playwright-report/` as an artifact.
5. Fails the build on test failure.

### Standard 5: Trace + video

After a test failure, the trace (`trace.zip`) and the video (`video.webm`) must be present under `frontend/test-results/`.

### Standard 6: Cross-link with FE-06

The `auth.ts` helper is shared with FE-06. Both upgrades must use the same login path (no parallel implementations).

---

## Detailed Implementation Plan

### Week 1 — Setup + login + navigation (Days 1-5)

**Day 1**
- [ ] Add `@playwright/test` to `devDependencies`.
- [ ] Run `npx playwright install --with-deps chromium`.
- [ ] Create `playwright.config.ts`.

**Day 2-3**
- [ ] Create `tests/e2e/_helpers/auth.ts`.
- [ ] Write `01_auth.spec.ts` (5 tests).
- [ ] Write `02_navigation.spec.ts` (7 tests).

**Day 4-5**
- [ ] Run locally; iterate until green.
- [ ] Wire into the C-01 pattern (single BrowserRouter).

### Week 2 — Evidence + reviews + roles + locale (Days 6-10)

**Day 6-7**
- [ ] Write `03_evidence.spec.ts` (6 tests).
- [ ] Write `04_reviews.spec.ts` (5 tests).

**Day 8-9**
- [ ] Write `05_roles.spec.ts` (5 tests).
- [ ] Write `06_locale.spec.ts` (4 tests).

**Day 10**
- [ ] Wire into CI (e2e job).
- [ ] Open a PR; verify the badge / artifact upload.
- [ ] Update `docs/TEST_STRATEGY.md` and `CHANGELOG.md`.

---

## Dependency Graph

```
@playwright/test in devDependencies
    ↓
playwright.config.ts
    ↓
auth.ts helper
    ↓
spec files (6)
    ↓
local green
    ↓
CI gating
    ↓
artifacts + docs
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Playwright installed; config merged | Frontend |
| CP-2 | `auth.ts` helper green | Frontend |
| CP-3 | Login + navigation green (12 tests) | Frontend |
| CP-4 | Evidence + reviews green (11 tests) | Frontend |
| CP-5 | Roles + locale green (9 tests) | Frontend |
| CP-6 | CI green | DevOps |
| CP-7 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If the runner cannot be installed in CI (e.g. no Docker) → fall back to a manual nightly job.
- If the auth helper is broken by a UI change → re-baseline FE-06 first; do not duplicate the helper.
- If total tests fall below 30 → re-open the test matrix.
