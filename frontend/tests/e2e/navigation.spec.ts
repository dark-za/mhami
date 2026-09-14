// filepath: frontend/tests/e2e/navigation.spec.ts
import { test, expect } from "@playwright/test";
import { installNetworkStubs } from "./bootstrap.js";
import { setLocale, setBootstrapRole } from "./fixtures";

/**
 * Browser/UI integration: the SPA boots under a single BrowserRouter so
 * navigation between every primary route completes without the
 * "cannot nest <BrowserRouter>" warning that broke production.
 */

test.beforeEach(async ({ page }) => {
  const warnings: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "warning" || msg.type() === "error") {
      warnings.push(msg.text());
    }
  });
  // Expose collected warnings to assertions.
  (page as unknown as { __warnings: string[] }).__warnings = warnings;
  await installNetworkStubs(page);
  await setBootstrapRole(page, "owner");
  await setLocale(page, "en");
});

test("home page loads without nested router warnings", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/$|\/login/);
  const warnings = (page as unknown as { __warnings: string[] }).__warnings;
  expect(warnings.some((w) => /cannot nest <BrowserRouter>/i.test(w))).toBe(false);
});

test("navigates to /evidence", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/evidence"]').first().click();
  await expect(page).toHaveURL(/\/evidence$/);
});

test("navigates to /people", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/people"]').first().click();
  await expect(page).toHaveURL(/\/people$/);
});

test("navigates to /reviews and shows translated headings", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/reviews"]').first().click();
  await expect(page).toHaveURL(/\/reviews$/);
  await expect(page.getByRole("heading", { name: "Queue, policy, and AI criteria" })).toBeVisible();
  await expect(page.getByText("The review queue is empty.")).toBeVisible();
});

test("navigates to /admin and shows AI control heading and labels", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/admin"]').first().click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("heading", { name: "Provider and enrollment" })).toBeVisible();
  await expect(page.getByText("MCP access").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Save provider" })).toBeVisible();
});

test("owner admin and operations render translated headings in Arabic", async ({ page }) => {
  await setLocale(page, "ar");
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "إعداد المزود وتسجيل الموصل" })).toBeVisible();
  await expect(page.getByRole("button", { name: "حفظ المزود" })).toBeVisible();
  await page.goto("/operations");
  await expect(page.getByRole("heading", { name: "سياسة التصدير وطلبات التنزيل" })).toBeVisible();
  await expect(page.getByText("لا توجد تصديرات بعد.")).toBeVisible();
  await expect(page.getByRole("button", { name: "حفظ سياسة التصدير" })).toBeVisible();
});

test("operations page shows export headings and non-empty labels", async ({ page }) => {
  await page.goto("/operations");
  await expect(page).toHaveURL(/\/operations$/);
  await expect(page.getByRole("heading", { name: "Policy and download requests" })).toBeVisible();
  await expect(page.getByText("No exports yet.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Save export policy" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create export" })).toBeVisible();
});

test("navigates to /dashboard", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/dashboard"]').first().click();
  await expect(page).toHaveURL(/\/dashboard$/);
  const completedToday = page.getByRole("region", { name: "Task and team summary" }).getByText("Completed today").locator("..");
  await expect(completedToday.getByText("7", { exact: true })).toBeVisible();
});

test("workspace remains within a mobile viewport", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Operational overview" })).toBeVisible();
  const layout = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, width: window.innerWidth }));
  expect(layout.scrollWidth).toBeLessThanOrEqual(layout.width);
});

test("dashboard uses Arabic labels when Arabic is selected", async ({ page }) => {
  await setLocale(page, "ar");
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "نظرة تشغيلية عامة" })).toBeVisible();
  await expect(page.getByText("المكتمل اليوم", { exact: true })).toBeVisible();
});
