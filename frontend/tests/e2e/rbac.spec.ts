/**
 * Role-based access control E2E.
 */
import { test, expect } from "@playwright/test";
import { setActiveRole, setLocale } from "./fixtures";

test.describe("FE-06 role-based access control", () => {
  test.beforeEach(async ({ page }) => {
    await setLocale(page, "en");
  });

  test("owner can access the admin route", async ({ page }) => {
    await setActiveRole(page, "owner");
    await page.goto("/admin");
    await expect(page).toHaveURL("/admin");
  });

  test("monitor can access reviews but not admin", async ({ page }) => {
    await setActiveRole(page, "monitor");
    await page.goto("/reviews");
    await expect(page).toHaveURL("/reviews");
    await page.goto("/admin");
    await expect(page.locator("text=/Access restricted|do not have access/i")).toBeVisible();
  });

  test("employee is restricted to tasks, evidence, operations, dashboard", async ({ page }) => {
    await setActiveRole(page, "employee");
    for (const path of ["/tasks", "/evidence", "/operations", "/dashboard"]) {
      await page.goto(path);
      await expect(page).toHaveURL(path);
    }
    for (const blocked of ["/people", "/reviews", "/admin"]) {
      await page.goto(blocked);
      await expect(page.locator("text=/Access restricted|do not have access/i")).toBeVisible();
    }
  });
});
