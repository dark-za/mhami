# C-01: Testing Strategy

> **Rule:** every test here must **pass in a real way** before considering C-01 completed.

## 1. Unit Tests (Unit Tests)

### 1.1 Full `App.test.tsx` Test

**File:** `frontend/src/__tests__/App.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { App } from '../App';

// Mock bootstrap snapshot
vi.mock('../design-system/tokens', () => ({
  bootstrapSnapshot: {
    company: { id: 'test', name: 'Test Co', locale: 'en' },
    currentUser: { id: 'user-1', role: 'owner' },
  },
}));

vi.mock('../api/bootstrap', () => ({
  createFallbackState: () => ({}),
}));

vi.mock('../hooks/useBootstrap', () => ({
  useBootstrap: () => ({
    state: { company: { name: 'Test Co' }, currentUser: { role: 'owner' } },
    loading: false,
    error: null,
    setState: vi.fn(),
  }),
}));

vi.mock('../hooks/useNotifications', () => ({
  useNotifications: () => ({ items: null, error: false }),
}));

describe('App', () => {
  it('renders without nested router warning', () => {
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    render(<App />);
    const nestedRouterWarnings = consoleWarn.mock.calls.filter(
      (call) => typeof call[0] === 'string' && call[0].includes('BrowserRouter')
    );
    expect(nestedRouterWarnings).toHaveLength(0);
    consoleWarn.mockRestore();
  });
});
```

**Run:**
```bash
cd frontend
npm run test
```

**Expected:** `1 passed`.

---

## 2. End-to-End Tests

### 2.1 Basic Navigation

**File:** `frontend/tests/e2e/navigation.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock auth
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('session', 'mock');
    });
  });

  test('home → tasks', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1, h2')).toContainText(/tasks/i);
  });

  test('home → evidence', async ({ page }) => {
    await page.goto('/evidence');
    await expect(page).toHaveURL('/evidence');
  });

  test('home → people', async ({ page }) => {
    await page.goto('/people');
    await expect(page).toHaveURL('/people');
  });

  test('home → reviews', async ({ page }) => {
    await page.goto('/reviews');
    await expect(page).toHaveURL('/reviews');
  });

  test('home → admin', async ({ page }) => {
    await page.goto('/admin');
    await expect(page).toHaveURL('/admin');
  });

  test('home → operations', async ({ page }) => {
    await page.goto('/operations');
    await expect(page).toHaveURL('/operations');
  });

  test('home → dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/dashboard');
  });
});
```

### 2.2 Internationalization (i18n)

```typescript
test.describe('Internationalization', () => {
  test('Arabic locale sets RTL', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="locale-ar"]');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
  });

  test('English locale sets LTR', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="locale-en"]');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  });

  test('Calendar preference persists', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="calendar-hijri"]');
    await page.reload();
    await expect(page.locator('[data-testid="calendar-active"]')).toContainText(/hijri/i);
  });
});
```

### 2.3 Roles

```typescript
test.describe('Role-based access', () => {
  test('Employee cannot access /admin', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('role', 'employee');
    });
    await page.goto('/admin');
    // Should be redirected or shown access denied
    await expect(page).not.toHaveURL('/admin');
  });

  test('Owner can access /admin', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('role', 'owner');
    });
    await page.goto('/admin');
    await expect(page).toHaveURL('/admin');
  });
});
```

---

## 3. Regression Tests

### 3.1 Login flow

```typescript
test('login → workspace', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="company_code"]', 'acme');
  await page.fill('[name="login_id"]', 'owner');
  await page.fill('[name="password"]', 'P@ssw0rd!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/');
});
```

### 3.2 Bootstrap loading

```typescript
test('shows loading state then content', async ({ page }) => {
  await page.goto('/');
  // Should show loading skeleton first
  // Then real content
  await expect(page.locator('[data-testid="bootstrap-loaded"]')).toBeVisible({ timeout: 5000 });
});
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| Unit tests | 1+ | all pass |
| E2E navigation | 7 | all pass |
| E2E i18n | 3 | all pass |
| E2E roles | 2 | all pass |
| E2E regression | 2 | all pass |
| **Total** | **15+** | **15+ passed** |

---

## 5. CI Integration

### 5.1 Update `.github/workflows/ci.yml`

Add a new job:

```yaml
  frontend-e2e:
    name: Frontend E2E Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: '24'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npx playwright install --with-deps chromium
      - run: cd frontend && npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## 6. Run tests locally

```bash
cd frontend

# Unit tests
npm run test

# E2E tests (requires dev server)
npm run test:e2e

# UI mode (interactive)
npm run test:e2e:ui

# HTML report
npx playwright show-report
```

---

## 7. Troubleshooting

### 7.1 "BrowserRouter not found"

**Cause:** Used `useNavigate` in a component not inside `<Router>`.
**Solution:** Ensure the component is within `AppShellHost` (inside `<App>` in main.tsx).

### 7.2 "Cannot read property 'push' of undefined"

**Cause:** Tried to call the history API directly instead of `useNavigate`.
**Solution:** Use `useNavigate()` from react-router.

### 7.3 E2E test hangs

**Cause:** `webServer` in `playwright.config.ts` does not work.
**Solution:** Run `npm run dev` manually in another terminal, then `npx playwright test`.
