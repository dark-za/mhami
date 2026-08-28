# FE-06: Playwright E2E Tests

## Discovery

### Status
- `frontend/src/tests/app.test.tsx` only
- tests `AppShell` with `MemoryRouter` (does not detect nested router)
- No E2E tests
- No browser tests

## Fix

### 1. Add Playwright

```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install --with-deps chromium
```

### 2. `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['github']],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
```

### 3. E2E Tests

**`tests/e2e/auth.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test('login with valid credentials', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="company_code"]', 'acme');
  await page.fill('[name="login_id"]', 'owner');
  await page.fill('[name="password"]', 'P@ssw0rd!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/');
});

test('login with invalid credentials shows error', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="company_code"]', 'acme');
  await page.fill('[name="login_id"]', 'wrong');
  await page.fill('[name="password"]', 'wrong');
  await page.click('button[type="submit"]');
  await expect(page.locator('.error')).toBeVisible();
});
```

**`tests/e2e/navigation.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    // login as owner
    await page.fill('[name="company_code"]', 'acme');
    await page.fill('[name="login_id"]', 'owner');
    await page.fill('[name="password"]', 'P@ssw0rd!');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('navigate to all sections', async ({ page }) => {
    for (const [name, path] of [
      ['Tasks', '/tasks'],
      ['Evidence', '/evidence'],
      ['People', '/people'],
      ['Reviews', '/reviews'],
      ['Admin', '/admin'],
      ['Operations', '/operations'],
      ['Dashboard', '/dashboard'],
    ] as const) {
      await page.click(`nav a[href="${path}"]`);
      await expect(page).toHaveURL(path);
    }
  });

  test('direct URL navigation works', async ({ page }) => {
    await page.goto('/people');
    await expect(page.locator('h1, h2')).toContainText(/people/i);
  });
});
```

**`tests/e2e/i18n.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test('Arabic locale sets RTL', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="locale-switcher"]');
  await page.click('text=Arabic');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
});

test('English locale sets LTR', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="locale-switcher"]');
  await page.click('text=English');
  await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
});
```

**`tests/e2e/rbac.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test('employee cannot access /admin', async ({ page }) => {
  // login as employee
  await page.goto('/login');
  await page.fill('[name="company_code"]', 'acme');
  await page.fill('[name="login_id"]', 'employee');
  await page.fill('[name="password"]', 'P@ssw0rd!');
  await page.click('button[type="submit"]');

  await page.goto('/admin');
  // Should redirect to / or show access denied
  await expect(page).not.toHaveURL('/admin');
});
```

**`tests/e2e/tasks.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test('view task list', async ({ page }) => {
  // login
  await page.goto('/login');
  await page.fill('[name="company_code"]', 'acme');
  await page.fill('[name="login_id"]', 'owner');
  await page.fill('[name="password"]', 'P@ssw0rd!');
  await page.click('button[type="submit"]');

  await page.goto('/tasks');
  // Wait for tasks to load
  await expect(page.locator('.task-list, [data-testid="empty-state"]')).toBeVisible();
});
```

### 4. CI Integration

In `.github/workflows/ci.yml`:
```yaml
  frontend-e2e:
    name: Frontend E2E
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

### Acceptance Standards
- AC-1: 20+ E2E tests
- AC-2: all pass in CI
- AC-3: HTML report generated
- AC-4: video on failure
- AC-5: categorized by: auth, navigation, i18n, rbac, tasks, evidence
