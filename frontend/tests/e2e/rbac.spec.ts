/**
 * Role-based access control E2E.
 *
 * The suite verifies RBAC behavior by mocking the /api/v1/bootstrap endpoint
 * with specific role configurations, rather than relying on localStorage role overrides.
 */
import { test, expect } from "@playwright/test";
import { installNetworkStubs } from "./bootstrap.js";
import { setLocale, setBootstrapRole } from "./fixtures";

test.describe("FE-06 role-based access control", () => {
  test.beforeEach(async ({ page }) => {
    await installNetworkStubs(page);
  });

  test("owner can access the admin route", async ({ page }) => {
    await setBootstrapRole(page, "owner");
    await setLocale(page, "en");
    await page.goto("/admin");
    await expect(page).toHaveURL("/admin");
  });

  test("monitor can access dashboard and reviews but not admin", async ({ page }) => {
    await setBootstrapRole(page, "monitor");
    await setLocale(page, "en");
    await page.goto("/dashboard");
    await expect(page).toHaveURL("/dashboard");
    await expect(page.getByRole("heading", { name: "Operational overview" })).toBeVisible();
    await page.goto("/reviews");
    await expect(page).toHaveURL("/reviews");
    await expect(page.getByRole("heading", { name: "Queue, policy, and AI criteria" })).toBeVisible();
    await page.goto("/admin");
    await expect(page.locator("text=/Access restricted|do not have access/i")).toBeVisible();
    await expect(page.getByText("Access restricted")).toBeVisible();
  });

  test("monitor denied admin shows Arabic restricted heading in RTL", async ({ page }) => {
    await setBootstrapRole(page, "monitor");
    await setLocale(page, "ar");
    await page.goto("/admin");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await expect(page.getByText("الوصول مقيّد")).toBeVisible();
    // Admin route uses nav.admin label as title, body is explainer with roles
    await expect(page.getByRole("heading", { name: "الإدارة" })).toBeVisible();
    await expect(page.getByText("هذه الصفحة مخصصة للأدوار التالية")).toBeVisible();
    // Non-empty state: still shows restricted, not provider heading
    await expect(page.getByRole("heading", { name: "Provider and enrollment" })).not.toBeVisible();
    await expect(page.getByRole("heading", { name: "إعداد المزود وتسجيل الموصل" })).not.toBeVisible();
  });

  test("employee may only access tasks and evidence, is blocked from dashboard", async ({ page }) => {
    await setBootstrapRole(page, "employee");
    await setLocale(page, "en");
    for (const path of ["/tasks", "/evidence"]) {
      await page.goto(path);
      await expect(page).toHaveURL(path);
    }
    for (const blocked of ["/dashboard", "/operations", "/people", "/reviews", "/admin"]) {
      await page.goto(blocked);
      await expect(page.locator("text=/Access restricted|do not have access/i")).toBeVisible();
    }
  });
});