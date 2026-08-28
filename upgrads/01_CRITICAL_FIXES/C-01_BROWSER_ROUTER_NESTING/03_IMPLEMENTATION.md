# C-01: Implementation Guide

> **Golden Rule:** every change in this file must be **documented with lines before and after**,
> and accompanied by a clear git diff.

## Step 1: Add Playwright for E2E tests

### 1.1 Update `frontend/package.json`

**Location:** `frontend/package.json`

```json
{
  "devDependencies": {
    "@playwright/test": "^1.48.0"
  },
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

### 1.2 Create `frontend/playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 1.3 Write the first E2E test

**New file:** `frontend/tests/e2e/navigation.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Navigation smoke tests', () => {
  test('home page loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL('/');
  });

  test('navigates to evidence', async ({ page }) => {
    await page.goto('/');
    await page.click('a[href="/evidence"]');
    await expect(page).toHaveURL('/evidence');
  });

  test('navigates to people', async ({ page }) => {
    await page.goto('/');
    await page.click('a[href="/people"]');
    await expect(page).toHaveURL('/people');
  });

  test('navigates to reviews', async ({ page }) => {
    await page.goto('/');
    await page.click('a[href="/reviews"]');
    await expect(page).toHaveURL('/reviews');
  });

  test('navigates to admin', async ({ page }) => {
    await page.goto('/');
    await page.click('a[href="/admin"]');
    await expect(page).toHaveURL('/admin');
  });
});
```

**Run the test before the fix:**

```bash
cd frontend
npm run test:e2e
```

**Expected output (before fix):**
```
Running 5 tests using 1 worker
  1) home page loads
  2) navigates to evidence
  3) navigates to people
  ...
5 failed
```

**Cause of failure:** Nested `<BrowserRouter>` disables React Router navigation.

---

## Step 2: Remove BrowserRouter from App.tsx

### 2.1 File before

**Location:** `frontend/src/App.tsx:1-166`

```tsx
import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";
// ❌ Remove: import BrowserRouter

import { AppShell } from "./shell/AppShell";
import { RoleGuard } from "./shell/RoleGuard";
// ...

function AppShellHost() {
  // ... stays as is, but becomes inside <App> and not inside <BrowserRouter>
}

export function App() {
  return (
    <BrowserRouter>  // ❌ Remove
      <AppShellHost />
    </BrowserRouter>  // ❌ Remove
  );
}
```

### 2.2 File after

**Location:** `frontend/src/App.tsx` (Modified)

```tsx
import { useState } from "react";
import { Navigate, Route, Routes } from "react-router";
// ✅ BrowserRouter removed from imports

import { AppShell } from "./shell/AppShell";
import { RoleGuard } from "./shell/RoleGuard";
// ... rest of the imports

function AppShellHost() {
  // ... same logic, but consumes Router context from main.tsx

  return (
    <AppShell
      bootstrap={state}
      setBootstrap={(updater) => setState((current) => updater(current))}
      loading={loading}
      loadError={error}
      locale={locale}
      setLocale={setLocale}
      calendar={calendar}
      setCalendar={setCalendar}
      role={role}
      setRole={setRole}
      notifications={notifications}
      notificationsError={notificationsError}
    >
      <Routes>
        {/* ... same Routes as before ... */}
      </Routes>
    </AppShell>
  );
}

export function App() {
  // ✅ No BrowserRouter here — the consumer is main.tsx
  return <AppShellHost />;
}
```

---

## Step 3: Ensure main.tsx contains one BrowserRouter

**Location:** `frontend/src/main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router";
import { App } from "./App";
import { AppErrorBoundary } from "./shell/AppErrorBoundary";
import "./styles.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppErrorBoundary>
          <App />
        </AppErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

**Change:** No change required — `main.tsx` is correct as is.

---

## Step 4: Run checks

### 4.1 Typecheck

```bash
cd frontend
npm run typecheck
```

**Expected output:** No errors, `exit code 0`.

### 4.2 Build

```bash
npm run build
```

**Expected output:**
```
vite v6.4.3 building for production...
✓ 112 modules transformed.
dist/index.html                   0.45 kB
dist/assets/index-xxx.js        450.12 kB
✓ built in 4.32s
```

### 4.3 E2E tests

```bash
npm run test:e2e
```

**Expected deliverables (After Fix):**
```
Running 5 tests using 1 worker
  ✓ home page loads (1.2s)
  ✓ navigates to evidence (0.8s)
  ✓ navigates to people (0.9s)
  ✓ navigates to reviews (0.7s)
  ✓ navigates to admin (0.8s)
5 passed (4.4s)
```

---

## Step 5: Recording results

Open `04_RESULTS.md` and record:

```markdown
## Results C-01: Fix BrowserRouter

| Command | Result | Exit Code |
|---|---|---|
| grep -c "BrowserRouter" | 1 | 0 |
| npm run typecheck | success | 0 |
| npm run build | success | 0 |
| npm run test:e2e | 5 passed | 0 |

## Git Changes
- (commit hash 1) Add Playwright config and E2E tests
- (commit hash 2) Remove nested BrowserRouter from App.tsx
- (commit hash 3) Update CHANGELOG.md
```

---

## Safety Checks

| Check | Command | Expected Result |
|---|---|---|
| No warnings in the console | `npm run dev` + DevTools | No warning |
| Outlet type is correct | `npm run typecheck` | 0 errors |
| locale state preserved | localStorage.getItem('locale') | correct value |
| calendar state preserved | localStorage.getItem('calendar') | correct value |
| bootstrap works | wait for the page to load | state.company.name |

---

## Rollback
