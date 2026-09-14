/**
 * Shared browser/UI helpers. Role fixtures stub bootstrap responses to exercise
 * shell rendering and navigation; they do not authenticate against a backend.
 */
import { expect, type Page } from "@playwright/test";

export async function setLocale(page: Page, locale: "en" | "ar") {
  await page.addInitScript((nextLocale) => {
    window.localStorage.setItem("mhami.locale", nextLocale);
  }, locale);
}

export async function setBootstrapRole(page: Page, role: "owner" | "monitor" | "employee") {
  const enabledModules =
    role === "employee"
      ? ["tasks", "evidence"]
      : role === "monitor"
        ? ["dashboard", "operations", "tasks", "evidence", "people", "reviews"]
        : ["dashboard", "operations", "tasks", "evidence", "people", "reviews", "admin", "agent_access"];

  await page.unroute("**/api/v1/bootstrap");
  await page.route("**/api/v1/bootstrap", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        installation: { setup_required: false },
        company: { id: "acme", name: "Acme", locale: "en" },
        current_user: { id: "user-1", role, display_name: "Test User", login_id: "test", is_authenticated: true },
        permissions: role === "owner" ? ["users.manage"] : role === "monitor" ? ["reviews.manage"] : ["tasks.execute"],
        enabled_modules: enabledModules,
        branches: [],
        branch_scope: [],
      }),
    });
  });
}

export async function expectDirection(page: Page, dir: "ltr" | "rtl") {
  await expect(page.locator("html")).toHaveAttribute("dir", dir);
}
