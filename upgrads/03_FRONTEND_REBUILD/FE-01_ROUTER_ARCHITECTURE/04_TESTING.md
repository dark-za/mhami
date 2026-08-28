# FE-01: Clean Router Architecture — Testing

## Unit tests
| File | Coverage |
|---|---|
| `src/tests/app.routes.test.tsx` | Verifies the shell boots under a single `BrowserRouter`, no nested-router warning, and the role override surfaces the People page. |
| `src/tests/app.test.tsx` | Smoke-tests the AppShell markup. |
| `src/tests/app.auth.test.tsx` | Verifies the `/login` and `/` routes mount the expected surfaces. |
| `src/routes/routes.test.tsx` | Drives the route table for owner, monitor, employee, and unknown paths. |

## E2E tests
| File | Coverage |
|---|---|
| `tests/e2e/navigation.spec.ts` | Asserts the SPA boots under a single BrowserRouter, every primary route mounts the expected surface, and an employee is blocked from `/admin`. |

## Manual checklist
- [x] `npm run typecheck` passes
- [x] `npm run test` passes (32 tests, 0 failures)
- [x] `npm run build` succeeds, with each page bundled into a separate
      chunk (Tasks, Evidence, People, Reviews, Admin, Operations,
      Pilot, Login)
- [x] `npm run test:e2e` is wired to Playwright but requires the
      Chromium binary (`npx playwright install --with-deps chromium`)

## CI evidence
The CI workflow runs:
1. `npm ci`
2. `npx playwright install --with-deps chromium`
3. `npm run test`
4. `npm run build`
5. `npm run test:e2e`
