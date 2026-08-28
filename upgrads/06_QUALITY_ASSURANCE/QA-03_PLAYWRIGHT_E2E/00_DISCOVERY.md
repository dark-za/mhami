# QA-03: Playwright E2E Tests

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The frontend has Vitest for unit tests but **no end-to-end browser tests**. There is no Playwright runner, no `playwright.config.ts`, and no `tests/e2e/` directory. The `00_SUMMARY.md` lists QA-03 as "covered in FE-06" but FE-06 has not delivered the runner either; both upgrades are blocked on the same configuration.

**Evidence gathered:**
- `frontend/package.json` does not list `@playwright/test` (or any browser runner).
- `frontend/tests/` contains only Vitest unit tests; no `e2e/` subfolder.
- `frontend/playwright.config.ts` does not exist.
- The C-01 plan describes the same E2E setup (5 navigation tests) but it has not been wired in either.

### Impact

| Dimension | Impact |
|---|---|
| Functional | C-01 (nested BrowserRouter) and FE-06 cannot be verified; navigation bugs ship. |
| Security | Login + CSRF + role redirects cannot be exercised end-to-end. |
| Operational | No automated smoke for `login → workspace → evidence → reviews`. |
| Compliance | Gate-D requires E2E evidence; this gap is a release blocker. |
| Financial | Manual regression sweeps before each release. |

### Reproducible Evidence

```bash
# 1. Confirm Playwright is not installed
Select-String -Path frontend\package.json -Pattern "@playwright"
# Expected today: 0 matches

# 2. Confirm playwright.config.ts is missing
Test-Path frontend\playwright.config.ts
# Expected today: False

# 3. Confirm e2e/ subfolder is missing
Test-Path frontend\tests\e2e
# Expected today: False

# 4. Confirm FE-06 status
Get-Content upgrads\03_FRONTEND_REBUILD\FE-06_E2E_TESTS\00_DISCOVERY.md
# Expected today: 00_DISCOVERY.md only, no implementation files
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Browser runner | none | Playwright (Chromium) |
| Configuration | none | `playwright.config.ts` |
| Test directory | none | `frontend/tests/e2e/` with `*.spec.ts` |
| Test count | 0 | ≥30 |
| CI integration | none | a job in `.github/workflows/ci.yml` that runs `npx playwright test` |
| Auth fixture | none | a helper that logs in and stores the session |
| Trace | none | `trace: "on-first-retry"` + `video: "retain-on-failure"` |

---

## 3. Goal Statement

> Within **2 weeks (coordinated with FE-06)**, install Playwright, create a working configuration, and ship **≥30 E2E tests** that cover login, navigation, evidence upload, review decisions, role-based access, and CSRF — wired into CI as a gating job.

### Acceptance Criteria

1. **AC-1:** `@playwright/test` is in `frontend/package.json` devDependencies.
2. **AC-2:** `frontend/playwright.config.ts` exists with Chromium as the only project, a `webServer` block that boots `npm run dev`, and trace/video retention.
3. **AC-3:** `frontend/tests/e2e/` exists with at least 5 spec files and 30 tests.
4. **AC-4:** `npx playwright test --reporter=line` exits 0 on a clean run.
5. **AC-5:** A CI job in `.github/workflows/ci.yml` runs `npx playwright test` against a real backend (`compose.dev.yml`) and uploads the HTML report.
6. **AC-6:** A `tests/e2e/_helpers/auth.ts` fixture logs in a user and stores the session for reuse across tests.
7. **AC-7:** Tests cover: login (success + failure), navigation, evidence upload (happy + size + signature), review decisions, role-based redirect, CSRF token presence, locale toggle, calendar preference, and logout.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Flaky tests due to network | High | High | Use `waitForLoadState` + `expect.toHaveURL`; avoid `sleep`. |
| Real backend in CI is heavy | Medium | Medium | Use `compose.dev.yml` with seeded data; cache Docker layers. |
| Login flow changes break tests | Medium | High | Drive login through a `auth.ts` helper, not raw selectors. |
| Browser binaries not installed | High | High | `npx playwright install --with-deps chromium` in CI. |
| Cross-link with FE-06 | Medium | Medium | Coordinate with FE-06 owner; share the `auth.ts` helper. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `@playwright/test` to devDependencies | Frontend | not-started |
| 2 | Create `playwright.config.ts` | Frontend | not-started |
| 3 | Create `tests/e2e/_helpers/auth.ts` | Frontend | not-started |
| 4 | Write `tests/e2e/01_auth.spec.ts` (login + logout) | Frontend | not-started |
| 5 | Write `tests/e2e/02_navigation.spec.ts` (5+ routes) | Frontend | not-started |
| 6 | Write `tests/e2e/03_evidence.spec.ts` (upload + size + signature) | Frontend | not-started |
| 7 | Write `tests/e2e/04_reviews.spec.ts` (decision flow) | Frontend | not-started |
| 8 | Write `tests/e2e/05_roles.spec.ts` (RBAC) | Frontend | not-started |
| 9 | Write `tests/e2e/06_locale.spec.ts` (AR/EN + calendar) | Frontend | not-started |
| 10 | Add `e2e` job to `.github/workflows/ci.yml` | DevOps | not-started |
| 11 | Run `npx playwright test` locally and confirm green | Frontend | not-started |
| 12 | Update `docs/TEST_STRATEGY.md` and `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [frontend/package.json](../../../frontend/package.json)
- [frontend/vite.config.ts](../../../frontend/vite.config.ts)
- [upgrads/03_FRONTEND_REBUILD/FE-06_E2E_TESTS](../../03_FRONTEND_REBUILD/FE-06_E2E_TESTS/00_DISCOVERY.md)
- [upgrads/01_CRITICAL_FIXES/C-01_BROWSER_ROUTER_NESTING](../../01_CRITICAL_FIXES/C-01_BROWSER_ROUTER_NESTING/03_IMPLEMENTATION.md) — share auth/navigation pattern
- [docs/TEST_STRATEGY.md](../../../docs/TEST_STRATEGY.md)
