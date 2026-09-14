import { test, expect } from "@playwright/test";
import { installNetworkStubs } from "./bootstrap.js";
import { setLocale } from "./fixtures";

// Real browser tabs, mocked server session. Backend expiry is covered by Django tests.
test("logging out in one tab removes the workspace from the other tab", async ({ page, context }) => {
  let signedIn = true;
  const other = await context.newPage();
  for (const tab of [page, other]) {
    await setLocale(tab, "en");
    await installNetworkStubs(tab);
    await tab.route("**/api/v1/bootstrap", route => route.fulfill({ json: {
      installation: { setup_required: false },
      current_user: signedIn ? { id: "owner", role: "owner", is_authenticated: true } : { is_authenticated: false },
      company: signedIn ? { id: "company", name: "Private Organization" } : null,
      permissions: [], branches: [], branch_scope: [], enabled_modules: signedIn ? ["tasks", "dashboard"] : [],
    } }));
    await tab.route("**/api/v1/auth/logout", async route => {
      signedIn = false;
      await route.fulfill({ status: 204 });
    });
    await tab.goto("/tasks");
    await expect(tab.getByRole("button", { name: "Sign out", exact: true })).toBeVisible();
  }
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  for (const tab of [page, other]) {
    await expect(tab).toHaveURL(/\/login$/);
    await expect(tab.getByRole("heading", { name: "Sign in to the workspace" })).toBeVisible();
    await expect(tab.getByRole("button", { name: "Sign out", exact: true })).toHaveCount(0);
  }
  await other.close();
});
