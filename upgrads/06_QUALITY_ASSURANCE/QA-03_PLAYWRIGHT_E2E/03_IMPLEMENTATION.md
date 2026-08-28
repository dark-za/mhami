# QA-03: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. The `auth.ts` helper is the single source of truth for login; do not duplicate it across spec files.

## Step 1: Add Playwright to `frontend/package.json`

### 1.1 File before

```json
{
  "devDependencies": {
    "typescript": "5.9.2",
    "vite": "6.4.3",
    "vitest": "3.2.7"
  }
}
```

### 1.2 File after

```json
{
  "devDependencies": {
    "@playwright/test": "^1.48.0",
    "typescript": "5.9.2",
    "vite": "6.4.3",
    "vitest": "3.2.7"
  },
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:install": "playwright install --with-deps chromium"
  }
}
```

**Install:**
```bash
cd frontend
npm install
npx playwright install --with-deps chromium
```

---

## Step 2: Create `playwright.config.ts`

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["html"], ["line"]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    API_URL: process.env.E2E_API_URL ?? "http://localhost:8000",
    trace: "on-first-retry",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: process.env.CI
    ? undefined
    : {
        command: "npm run dev",
        url: "http://localhost:5173",
        reuseExistingServer: true,
      },
});
```

**Verify:**
```bash
Test-Path frontend\playwright.config.ts
# Expected: True
```

---

## Step 3: Auth helper

### 3.1 New file: `frontend/tests/e2e/_helpers/auth.ts`

```ts
import { Page, expect } from "@playwright/test";

const credentials = {
  owner:       { company_code: "acme",     login_id: "owner",     password: "P@ssw0rd!" },
  manager:     { company_code: "acme",     login_id: "manager",   password: "P@ssw0rd!" },
  supervisor:  { company_code: "acme",     login_id: "supervisor", password: "P@ssw0rd!" },
  employee:    { company_code: "acme",     login_id: "employee",  password: "P@ssw0rd!" },
};

export async function login(page: Page, role: keyof typeof credentials): Promise<void> {
  const c = credentials[role];
  await page.goto("/login");
  await page.fill('[name="company_code"]', c.company_code);
  await page.fill('[name="login_id"]', c.login_id);
  await page.fill('[name="password"]', c.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL("/");
}

export async function logout(page: Page): Promise<void> {
  await page.click('[data-testid="logout"]');
  await expect(page).toHaveURL("/login");
}
```

---

## Step 4: Spec files

### 4.1 `01_auth.spec.ts` (5 tests)

```ts
import { test, expect } from "@playwright/test";
import { login, logout } from "./_helpers/auth";

test("login success", async ({ page }) => {
  await login(page, "owner");
});

test("login with wrong password shows error", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[name="company_code"]', "acme");
  await page.fill('[name="login_id"]', "owner");
  await page.fill('[name="password"]', "wrong");
  await page.click('button[type="submit"]');
  await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
});

test("locked account is rejected", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[name="company_code"]', "acme");
  await page.fill('[name="login_id"]', "locked");
  await page.fill('[name="password"]', "P@ssw0rd!");
  await page.click('button[type="submit"]');
  await expect(page.locator('[data-testid="login-error"]')).toContainText(/locked/i);
});

test("CSRF token present in form", async ({ page }) => {
  await page.goto("/login");
  const token = await page.locator('input[name="csrfmiddlewaretoken"]').count();
  expect(token).toBeGreaterThan(0);
});

test("logout returns to /login", async ({ page }) => {
  await login(page, "owner");
  await logout(page);
});
```

### 4.2 `02_navigation.spec.ts` (7 tests)

```ts
import { test, expect } from "@playwright/test";
import { login } from "./_helpers/auth";

test.beforeEach(async ({ page }) => { await login(page, "owner"); });

const routes = ["/", "/tasks", "/evidence", "/people", "/reviews", "/admin", "/operations", "/dashboard"];

for (const r of routes) {
  test(`navigates to ${r}`, async ({ page }) => {
    await page.goto(r);
    await expect(page).toHaveURL(r);
  });
}
```

### 4.3 `03_evidence.spec.ts` (6 tests)

```ts
import { test, expect } from "@playwright/test";
import { login } from "./_helpers/auth";

test.beforeEach(async ({ page }) => { await login(page, "owner"); });

test("upload happy path", async ({ page }) => {
  await page.goto("/evidence");
  await page.setInputFiles('input[type="file"]', "tests/e2e/fixtures/sample.jpg");
  await page.click('button[type="submit"]');
  await expect(page.locator('[data-testid="upload-success"]')).toBeVisible();
});

test("oversized upload rejected", async ({ page }) => {
  await page.goto("/evidence");
  await page.setInputFiles('input[type="file"]', "tests/e2e/fixtures/big.jpg");
  await expect(page.locator('[data-testid="upload-error"]')).toContainText(/too large/i);
});

test("signature mismatch rejected", async ({ page }) => {
  await page.goto("/evidence");
  await page.setInputFiles('input[type="file"]', "tests/e2e/fixtures/bad-sig.jpg");
  await expect(page.locator('[data-testid="upload-error"]')).toContainText(/signature/i);
});

test("missing CSRF rejected", async ({ page }) => {
  await page.goto("/evidence");
  await page.evaluate(() => document.querySelectorAll('input[name="csrfmiddlewaretoken"]').forEach(n => n.remove()));
  await page.setInputFiles('input[type="file"]', "tests/e2e/fixtures/sample.jpg");
  await page.click('button[type="submit"]');
  await expect(page.locator('[data-testid="upload-error"]')).toContainText(/csrf/i);
});

test("evidence list page loads", async ({ page }) => {
  await page.goto("/evidence");
  await expect(page.locator('h1, h2')).toContainText(/evidence/i);
});

test("evidence detail page loads", async ({ page }) => {
  await page.goto("/evidence");
  await page.click('a[href*="/evidence/"]');
  await expect(page).toHaveURL(/\/evidence\/.+/);
});
```

### 4.4 `04_reviews.spec.ts` (5 tests)

```ts
import { test, expect } from "@playwright/test";
import { login } from "./_helpers/auth";

test.beforeEach(async ({ page }) => { await login(page, "owner"); });

test("open a review decision", async ({ page }) => {
  await page.goto("/reviews");
  await page.click('a[href*="/reviews/"]');
  await expect(page).toHaveURL(/\/reviews\/.+/);
});

test("approve a decision", async ({ page }) => {
  await page.goto("/reviews");
  await page.click('a[href*="/reviews/"]');
  await page.click('[data-testid="approve"]');
  await expect(page.locator('[data-testid="decision-status"]')).toContainText(/approved/i);
});

test("reject a decision with reason", async ({ page }) => {
  await page.goto("/reviews");
  await page.click('a[href*="/reviews/"]');
  await page.click('[data-testid="reject"]');
  await page.fill('[name="reason"]', "Insufficient evidence");
  await page.click('[data-testid="submit-reject"]');
  await expect(page.locator('[data-testid="decision-status"]')).toContainText(/rejected/i);
});

test("comment on a decision", async ({ page }) => {
  await page.goto("/reviews");
  await page.click('a[href*="/reviews/"]');
  await page.fill('[name="comment"]', "Please attach more context");
  await page.click('[data-testid="add-comment"]');
  await expect(page.locator('[data-testid="comments"]')).toContainText(/attach more context/i);
});

test("decision history visible", async ({ page }) => {
  await page.goto("/reviews");
  await page.click('a[href*="/reviews/"]');
  await expect(page.locator('[data-testid="history"]')).toBeVisible();
});
```

### 4.5 `05_roles.spec.ts` (5 tests)

```ts
import { test, expect } from "@playwright/test";
import { login } from "./_helpers/auth";

test("owner can access /admin", async ({ page }) => {
  await login(page, "owner");
  await page.goto("/admin");
  await expect(page).toHaveURL("/admin");
});

test("employee blocked from /admin", async ({ page }) => {
  await login(page, "employee");
  await page.goto("/admin");
  await expect(page).not.toHaveURL("/admin");
});

test("manager limited to branch", async ({ page }) => {
  await login(page, "manager");
  await page.goto("/people");
  await expect(page.locator('h1, h2')).toContainText(/people/i);
});

test("supervisor read-only on /reviews", async ({ page }) => {
  await login(page, "supervisor");
  await page.goto("/reviews");
  await expect(page.locator('[data-testid="approve"]')).toHaveCount(0);
});

test("outsider redirected to /login", async ({ page }) => {
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/login/);
});
```

### 4.6 `06_locale.spec.ts` (4 tests)

```ts
import { test, expect } from "@playwright/test";
import { login } from "./_helpers/auth";

test.beforeEach(async ({ page }) => { await login(page, "owner"); });

test("English sets LTR", async ({ page }) => {
  await page.click('[data-testid="locale-en"]');
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("Arabic sets RTL", async ({ page }) => {
  await page.click('[data-testid="locale-ar"]');
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
});

test("Hijri calendar persists", async ({ page }) => {
  await page.click('[data-testid="calendar-hijri"]');
  await page.reload();
  await expect(page.locator('[data-testid="calendar-active"]')).toContainText(/hijri/i);
});

test("Gregorian calendar persists", async ({ page }) => {
  await page.click('[data-testid="calendar-gregorian"]');
  await page.reload();
  await expect(page.locator('[data-testid="calendar-active"]')).toContainText(/gregorian/i);
});
```

**Verify:**
```bash
cd frontend
npx playwright test --list 2>&1 | Select-Object -Last 3
# Expected: >= 30 specs collected
```

---

## Step 5: Run locally

```bash
# 1. Start the backend stack
cd compose
docker compose -f compose.dev.yml up -d backend
cd ../frontend

# 2. Seed test data (per docs/PILOT_PROFILE.md)
docker compose -f compose.dev.yml exec backend python manage.py loaddata fixtures/seed.json

# 3. Run E2E
npx playwright test --reporter=line
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## Step 6: CI workflow

### 6.1 Update `.github/workflows/ci.yml` — add an `e2e` job

```yaml
  e2e:
    runs-on: ubuntu-latest
    services:
      postgres: { ... }
      redis:    { ... }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - name: Install backend
        run: pip install -r backend/requirements.txt
      - name: Migrate
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_test }
        run: cd backend && python manage.py migrate
      - name: Seed
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_test }
        run: cd backend && python manage.py loaddata fixtures/seed.json
      - name: Start backend
        run: cd backend && python manage.py runserver 0.0.0.0:8000 &
      - name: Install frontend
        run: npm ci --prefix frontend
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      - name: E2E
        env:
          E2E_BASE_URL: http://localhost:5173
          E2E_API_URL: http://localhost:8000
        run: |
          cd frontend
          npm run dev &
          npx wait-on http://localhost:5173
          npx playwright test --reporter=line
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report
```

**Verify:**
```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "playwright"
# Expected: 1+ match
```

---

## Step 7: Documentation

1. Update `docs/TEST_STRATEGY.md` with the new spec files and the `e2e` job.
2. Update `CHANGELOG.md` with a `QA-03` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Playwright present | `grep @playwright frontend/package.json` | match |
| Config exists | `Test-Path frontend/playwright.config.ts` | True |
| Spec count | `npx playwright test --list` | ≥30 |
| Local green | `npx playwright test --reporter=line` | exit 0 |
| CI step | `grep playwright .github/workflows/ci.yml` | match |
| Typecheck | `npm run typecheck` | exit 0 |
| Build | `npm run build` | exit 0 |

---

## Rollback

```bash
git revert <qa03-commit-sha>
cd frontend
npm install
npx playwright test --list
# Expected: 0 (or only the pre-existing FE-06 specs)
```
