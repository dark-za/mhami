# C-01: Fix Nested BrowserRouter (Nested Router Bootstrap Blocker)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The frontend contains a `BrowserRouter` nested at two levels, which prevents the application from booting in production.

**Evidence gathered:**
- `frontend/src/main.tsx:14-18` — Outer level:
  ```tsx
  <BrowserRouter>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </BrowserRouter>
  ```
- `frontend/src/App.tsx:160-164` — Inner level (duplicate):
  ```tsx
  export function App() {
    return (
      <BrowserRouter>
        <AppShellHost />
      </BrowserRouter>
    );
  }
  ```

**Result:** React Router 7.x issues an explicit warning when `BrowserRouter` is nested, and disables the navigation of nested routes. The only test in `frontend/src/tests/app.test.tsx` tests `AppShell` only with `MemoryRouter`, which hides the issue.

### Impact

| Dimension | Impact |
|---|---|
| Functional | The application does not boot in production. Navigation does not work. |
| Security | No direct security impact. |
| Operational | E2E cannot be tested because the application does not load. |
| Usability | Complete failure in production launch. |
| Financial | Launch delay with daily cost. |

### Reproducible Evidence

```bash
# Verification command 1: Confirm presence of nested router
Select-String -Path frontend/src/main.tsx -Pattern "BrowserRouter"
Select-String -Path frontend/src/App.tsx -Pattern "BrowserRouter"

# Verification command 2: Run the application
cd frontend
npm run dev
# warnings will appear "You cannot nest <BrowserRouter>" in the console

# Verification command 3: E2E test
npx playwright test
# will fail with "page cannot navigate"
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Number of BrowserRouters | 2 (duplicated) | 1 (unified) |
| Router location | main.tsx + App.tsx | main.tsx only |
| Routes structure | in AppShellHost (nested) | in App (main) |
| Warning | Yes | No |
| Testing the full App | not possible | possible |

---

## 3. Goal Statement

> Unify `BrowserRouter` at a single level (`main.tsx`), with the move of `Routes` entirely to `App`, and ensure that `AppShellHost` becomes **a consumer** of the Router context, not a creator of it.

### Acceptance Criteria

1. **AC-1:** No warning appears `cannot nest <BrowserRouter>` in the console.
2. **AC-2:** Navigation between pages works (Tasks → Evidence → People → Reviews).
3. **AC-3:** At least one E2E test passes successfully (`npx playwright test`).
4. **AC-4:** `App.test.tsx` tests `<App />` fully, not `AppShell` only.
5. **AC-5:** No regression in existing features (Login, Bootstrap, Locale).
6. **AC-6:** `npm run typecheck` passes without errors.
7. **AC-7:** `npm run build` passes without errors.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Break existing routes | Medium | High | E2E tests + Review |
| Locale/Calendar state disruption | Low | Medium | Preserve state in App |
| Difficulty tracking useNavigate | Low | Low | Keep the same API |

---

## 5. Subtasks

| # | Task | Status |
|---|---|---|
| 1 | Write an E2E test that reflects the issue | not-started |
| 2 | Remove BrowserRouter from App.tsx | not-started |
| 3 | Move Routes from AppShellHost to App | not-started |
| 4 | Update AppShellHost to consume Router context | not-started |
| 5 | Run E2E and verify | not-started |
| 6 | Document the change in CHANGELOG | not-started |

---

## 6. References

- [React Router 7 docs - nesting](https://reactrouter.com/start/framework/routing)
- [App.tsx](../../../frontend/src/App.tsx)
- [main.tsx](../../../frontend/src/main.tsx)
- [app.test.tsx](../../../frontend/src/tests/app.test.tsx)
