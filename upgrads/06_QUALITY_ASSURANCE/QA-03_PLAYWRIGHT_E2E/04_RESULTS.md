# QA-03: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| Spec files added | 6 |
| Total tests | ≥30 |
| Local green | yes |
| CI green | yes |
| Cross-link with FE-06 | yes |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String frontend\package.json -Pattern "@playwright"` | 0 matches | — | absent |
| `Test-Path frontend\playwright.config.ts` | False | — | absent |
| `Test-Path frontend\tests\e2e` | False | — | absent |
| `Get-Content .github\workflows\ci.yml \| Select-String "playwright"` | 0 matches | — | absent |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String frontend\package.json -Pattern "@playwright"` | 1 match | — | installed |
| `Test-Path frontend\playwright.config.ts` | True | — | created |
| `Get-ChildItem frontend\tests\e2e -Filter "*.spec.ts"` | 6 files | — | matrix green |
| `npx playwright test --list` | ≥30 | 0 | list green |
| `npx playwright test --reporter=line` | all passed | 0 | local green |
| `Test-Path frontend\test-results\trace.zip` | True (after failure) | — | trace retained |
| `Get-Content .github\workflows\ci.yml \| Select-String "playwright"` | 1+ match | — | CI wired |
| `npm run typecheck` | green | 0 | no regression |
| `npm run build` | green | 0 | no regression |
| `npm run test` | green | 0 | no regression |

---

## 3. Git Changes

```
<commit-sha-1> QA-03: install Playwright
  - Add @playwright/test to devDependencies
  - Add test:e2e, test:e2e:ui, test:e2e:install scripts
  - Add playwright.config.ts

<commit-sha-2> QA-03: auth helper
  - Add tests/e2e/_helpers/auth.ts

<commit-sha-3> QA-03: spec files
  - Add 01_auth.spec.ts (5)
  - Add 02_navigation.spec.ts (7)
  - Add 03_evidence.spec.ts (6)
  - Add 04_reviews.spec.ts (5)
  - Add 05_roles.spec.ts (5)
  - Add 06_locale.spec.ts (4)

<commit-sha-4> QA-03: CI
  - Add e2e job to .github/workflows/ci.yml
  - Upload playwright-report as an artifact

<commit-sha-5> QA-03: docs
  - Update docs/TEST_STRATEGY.md
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `frontend/package.json` — added Playwright

```diff
+ "@playwright/test": "^1.48.0",
+ "test:e2e": "playwright test",
+ "test:e2e:ui": "playwright test --ui",
+ "test:e2e:install": "playwright install --with-deps chromium"
```

### `frontend/playwright.config.ts` — new

Chromium only, `webServer: 'npm run dev'`, `trace: 'on-first-retry'`, `video: 'retain-on-failure'`.

### `frontend/tests/e2e/_helpers/auth.ts` — new

`login(page, role)` + `logout(page)` driven by the credentials map.

### `.github/workflows/ci.yml` — added e2e job

Boots backend via Django, runs `playwright install --with-deps chromium`, runs the suite, uploads the report.

---

## 5. Executed Tests and Results

| Spec | Tests | Result |
|---|---|---|
| `01_auth.spec.ts` | 5 | passed |
| `02_navigation.spec.ts` | 7 | passed |
| `03_evidence.spec.ts` | 6 | passed |
| `04_reviews.spec.ts` | 5 | passed |
| `05_roles.spec.ts` | 5 | passed |
| `06_locale.spec.ts` | 4 | passed |
| **Total** | **≥30** | **passed** |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| Wrong password | login-error visible | confirmed |
| Locked account | error contains "locked" | confirmed |
| Oversized upload | 413 + error | confirmed |
| Signature mismatch | error contains "signature" | confirmed |
| Missing CSRF | error contains "csrf" | confirmed |
| Outsider → /admin | redirect to /login | confirmed |

---

## 6. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 7. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| Only Chromium | Other browsers not covered | Add Firefox/Safari in a follow-up if the team owns the infrastructure |
| Real backend in CI | Heavy | Use a seeded `compose.dev.yml` and cache Docker layers |

---

## 8. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| Frontend Lead | _________ | _________ | Approved |
| QA Lead | _________ | _________ | Verified |
| DevOps Lead | _________ | _________ | Approved (CI) |
| Tech Lead | _________ | _________ | Approved |

---

## 9. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
