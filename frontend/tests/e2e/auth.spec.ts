/** Authentication smoke coverage for the password-only local installation. */
import { test, expect } from "@playwright/test";

import { installUnauthenticatedNetworkStubs } from "./bootstrap.js";
import { setLocale, expectDirection } from "./fixtures";

test("landing page defaults to Arabic login form and RTL", async ({ page }) => {
  await installUnauthenticatedNetworkStubs(page);
  await page.goto("/");
  await expectDirection(page, "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.getByLabel("معرّف الدخول").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "تسجيل الدخول إلى مساحة العمل" })).toBeVisible();
});

test("landing page preserves explicit English locale and LTR", async ({ page }) => {
  await setLocale(page, "en");
  await installUnauthenticatedNetworkStubs(page);
  await page.goto("/");
  await expectDirection(page, "ltr");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByLabel("Login ID").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sign in to the workspace" })).toBeVisible();
  await page.reload();
  await expectDirection(page, "ltr");
  await expect(page.getByLabel("Login ID").first()).toBeVisible();
});

test("login page is reachable in Arabic by default", async ({ page }) => {
  await installUnauthenticatedNetworkStubs(page);
  await page.goto("/login");
  await expectDirection(page, "rtl");
  await expect(page.getByLabel("معرّف الدخول").first()).toBeVisible();
});

test("login page is reachable in explicit English and persists", async ({ page }) => {
  await setLocale(page, "en");
  await installUnauthenticatedNetworkStubs(page);
  await page.goto("/login");
  await expectDirection(page, "ltr");
  await expect(page.getByLabel("Login ID").first()).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Login ID").first()).toBeVisible();
  await expectDirection(page, "ltr");
});

test("Arabic login keeps credentials left-to-right within the RTL page", async ({ page }) => {
  await setLocale(page, "ar");
  await installUnauthenticatedNetworkStubs(page);
  await page.goto("/login");

  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.getByLabel("معرّف الدخول")).toHaveAttribute("dir", "ltr");
  await expect(page.getByLabel("كلمة المرور", { exact: true })).toHaveAttribute("dir", "ltr");
});

test("setup page defaults to Arabic when installation requires setup", async ({ page }) => {
  await page.route("**/api/v1/bootstrap", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        installation: { setup_required: true },
        current_user: { is_authenticated: false },
        company: null,
        permissions: [],
        branches: [],
        branch_scope: [],
        enabled_modules: [],
      }),
    });
  });
  await page.route("**/api/v1/notifications**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ notifications: [] }) });
  });
  await page.goto("/setup");
  await expectDirection(page, "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.getByRole("heading", { name: "إعداد منشأتك" })).toBeVisible();
  await expect(page.getByLabel("اسم المنشأة")).toBeVisible();
});

test("setup page preserves explicit English and persists after reload", async ({ page }) => {
  await setLocale(page, "en");
  await page.route("**/api/v1/bootstrap", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        installation: { setup_required: true },
        current_user: { is_authenticated: false },
        company: null,
        permissions: [],
        branches: [],
        branch_scope: [],
        enabled_modules: [],
      }),
    });
  });
  await page.route("**/api/v1/notifications**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ notifications: [] }) });
  });
  await page.goto("/setup");
  await expectDirection(page, "ltr");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { name: "Set up your organization" })).toBeVisible();
  await page.reload();
  await expectDirection(page, "ltr");
  await expect(page.getByRole("heading", { name: "Set up your organization" })).toBeVisible();
});

test("login Arabic persists after reload by default", async ({ page }) => {
  await installUnauthenticatedNetworkStubs(page);
  await page.goto("/login");
  await expectDirection(page, "rtl");
  await page.reload();
  await expectDirection(page, "rtl");
  await expect(page.getByLabel("معرّف الدخول").first()).toBeVisible();
});

test("owner enters the workspace after password login", async ({ page }) => {
  let signedIn = false;

  await setLocale(page, "en");

  await page.route("**/api/v1/bootstrap", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        signedIn
          ? {
              installation: { setup_required: false },
              company: { id: "acme", name: "Acme", locale: "en" },
              current_user: { id: "owner-1", role: "owner", is_authenticated: true },
              permissions: ["admin"],
              branches: [],
              branch_scope: [],
              enabled_modules: ["dashboard"],
            }
          : {
              installation: { setup_required: false },
              current_user: { is_authenticated: false },
              company: null,
              permissions: [],
              branches: [],
              branch_scope: [],
              enabled_modules: [],
            },
      ),
    });
  });
  await page.route("**/api/v1/auth/login", async (route) => {
    signedIn = true;
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
  });
  await page.route("**/api/v1/notifications**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ notifications: [] }) });
  });
  await page.route("**/api/v1/reviews/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ company: { id: "acme", name: "Acme", code: "acme", status: "active" }, summary: { completed_today: 7, overdue: 0, quality_exceptions: 0, pending: 2, in_progress: 1, cancelled: 0, employees: 3, monitors: 1, branches: 2, completed_in_period: 7 }, branches: [], period: "day", trend: [] }),
    });
  });

  await page.goto("/login");
  await page.getByLabel("Login ID").fill("owner");
  await page.getByLabel("Password", { exact: true }).fill("ValidOwnerPassword2026!");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
});
