# C-01: Goal and Plan (Goal & Plan)

## SMART Goal

> Within **5 working days**, unify `BrowserRouter` in `main.tsx` only,
> ensuring that **5/5 E2E Tests** succeed for navigating between all main routes.

## Detailed Acceptance Standards

### Standard 1: Only one BrowserRouter exists

**Test:**
```bash
grep -rn "BrowserRouter" frontend/src/ | wc -l
```
**Minimum threshold:** `1`

### Standard 2: Functional Navigation

**Manual test:**
- Open `/` → the tasks page appears
- Click on "Evidence" → navigates to `/evidence`
- Click on "People" → navigates to `/people`
- Click on "Reviews" → navigates to `/reviews`

### Standard 3: E2E tests

**File:** `frontend/tests/e2e/navigation.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test('navigates between all main routes', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL('/');

  await page.click('a[href="/evidence"]');
  await expect(page).toHaveURL('/evidence');

  await page.click('a[href="/people"]');
  await expect(page).toHaveURL('/people');

  await page.click('a[href="/reviews"]');
  await expect(page).toHaveURL('/reviews');

  await page.click('a[href="/admin"]');
  await expect(page).toHaveURL('/admin');
});

test('locale switching updates direction', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="locale-toggle"]');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
});

test('login flow reaches workspace', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="company_code"]', 'acme');
  await page.fill('[name="login_id"]', 'owner');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/');
});
```

### Standard 4: TypeScript compilation

```bash
cd frontend && npm run typecheck
```

**Threshold:** `exit code 0`, 0 errors.

### Standard 5: Build

```bash
cd frontend && npm run build
```

**Threshold:** `exit code 0`, `dist/` is created.

---

## Detailed Implementation Plan

### Day 1: Preparation

**Morning (4 hours):**
- [ ] Add Playwright as a dev dependency
- [ ] Write 3 E2E tests that reflect the correct behavior
- [ ] Run `npm run dev` and capture a screenshot of the issue

**Afternoon (4 hours):**
- [ ] Review `AppShellHost` and `AppShell` to identify the state that needs to be lifted
- [ ] Identify navigation icons and links in `AppShell`

### Days 2-3: Implementation

**Day 2:**
- [ ] Remove `BrowserRouter` from `App.tsx`
- [ ] Move `<Routes>` and `<Route>` from `AppShellHost` to `App`
- [ ] Modify `AppShellHost` to become a consumer of `Outlet` instead of `Routes`
- [ ] Update `AppShell` to receive `Outlet` prop

**Day 3:**
- [ ] Run `npm run typecheck`
- [ ] Run `npm run build`
- [ ] Run `npm run dev` manually

### Day 4: Verification

- [ ] Run E2E Tests
- [ ] manual test for each route
- [ ] Verify locale/calendar
- [ ] Record results in `04_RESULTS.md`

### Day 5: Documentation

- [ ] Update `CHANGELOG.md`
- [ ] Update `docs/FRONTEND_GAP_PLAN.md`
- [ ] final review with Frontend Lead
- [ ] Sign-off

---

## Dependency Graph

```
E2E tests ← currently fails due to nested router
    ↓
Remove BrowserRouter from App.tsx
    ↓
Move Routes to App
    ↓
Modify AppShell to receive Outlet
    ↓
typecheck → build → E2E tests
    ↓
Documentation + sign-off
```

---

## Checkpoints

| Point | Condition | Owner |
|---|---|---|
| CP-1 | E2E tests written and failing | Frontend Dev |
| CP-2 | BrowserRouter unified | Frontend Dev |
| CP-3 | Routes navigate successfully | Frontend Dev |
| CP-4 | typecheck/build passes | Frontend Lead |
| CP-5 | E2E tests succeed | QA Lead |
| CP-6 | Documentation updated | Tech Writer |
| CP-7 | Approved | Frontend Lead |

---

## Cancellation Criteria

- If the fix requires more than 5 working days
- If any other feature breaks
- If E2E cannot run due to the current test structure
- If large migration requirements emerge
