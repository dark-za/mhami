# FE-06: Playwright E2E Tests — Testing

## E2E tests
| File | Coverage |
|---|---|
| `tests/e2e/navigation.spec.ts` | Asserts the SPA boots under a single BrowserRouter and every primary route mounts the expected surface. |
| `tests/e2e/rbac.spec.ts` | Owner, monitor, and employee access to the primary routes. |
| `tests/e2e/i18n.spec.ts` | Locale switching and RTL/LTR flip. |
| `tests/e2e/auth.spec.ts` | Login page rendering and CSRF header on submit. |
| `tests/e2e/tasks.spec.ts` | Tasks page lifecycle. |
| `tests/e2e/evidence.spec.ts` | Evidence route mount. |
| `tests/e2e/reviews.spec.ts` | Reviews route mount. |

## Running the suite
```bash
npx playwright install --with-deps chromium
npm run test:e2e
```

## CI integration
The CI workflow installs chromium, runs `npm run test:e2e`, and
uploads the `playwright-report/` and `test-results/` artefacts.
