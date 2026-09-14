// filepath: frontend/tests/e2e/README.md
# Browser/UI Integration Tests

Playwright-based browser/UI integration suite for the workspace shell.

## Running locally

```bash
# 1. Install Playwright browsers (chromium only is required for the suite)
npx playwright install --with-deps chromium

# 2. Start the dev server (or let `webServer` start it for you)
npm run dev

# 3. Run the suite
npm run test:e2e
```

## Structure

| File | Surface |
|---|---|
| `auth.spec.ts` | Login page rendering, CSRF header on submit |
| `navigation.spec.ts` | Route table mounts every primary surface |
| `rbac.spec.ts` | Role-based access control per role |
| `i18n.spec.ts` | Locale switching + RTL/LTR flip |
| `tasks.spec.ts` | Tasks page lifecycle |
| `evidence.spec.ts` | Evidence route mount |
| `reviews.spec.ts` | Reviews route mount |

## Testing Notes

This is a browser/UI integration test suite with mocked API endpoints:

- All tests mock `/api/v1/bootstrap`, `/api/v1/auth/login`, and other required endpoints
- Tests verify the shell's behavior without a real Django backend
- Role behavior is tested via authenticated bootstrap responses, not localStorage overrides
- i18n direction tests explicitly set locale through UI or test setup to ensure reliability

## CI

The CI step must install chromium, run `npm run test:e2e`, and upload
the `playwright-report/` and `test-results/` artefacts.
