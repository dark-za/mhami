# FE-04: P0/P1 Workflow Screens — Goal

## Objective
Provide a coherent set of P0 (login, bootstrap, role nav, locale,
calendar) and P1 (tasks, evidence, reviews, notifications) screens
with consistent loading, empty, and error states.

## Acceptance criteria
1. The P0 surfaces (Login, Bootstrap, Role nav, Locale, Calendar) are
   all implemented and accessible.
2. The P1 surfaces (Tasks, Evidence, Reviews, Notifications) follow the
   same loading/empty/error contract.
3. Every page renders through the `AsyncState` helper so the user
   experience is consistent.
4. Every page exposes ARIA attributes for screen readers.
5. E2E specs cover the five critical paths.
