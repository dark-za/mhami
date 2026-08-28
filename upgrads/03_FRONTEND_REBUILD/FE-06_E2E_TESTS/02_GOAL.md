# FE-06: Playwright E2E Tests — Goal

## Objective
Add a Playwright-based end-to-end suite that exercises the primary
routes, role-based access, locale switching, and the login form so the
workspace shell is continuously validated.

## Acceptance criteria
1. Playwright is configured to use the local Vite dev server.
2. The E2E suite covers navigation, RBAC, i18n, auth, tasks,
   evidence, and reviews.
3. The HTML reporter is enabled and the trace/screenshot artefacts
   are retained on failure.
4. CI runs the suite and uploads the artefacts.
