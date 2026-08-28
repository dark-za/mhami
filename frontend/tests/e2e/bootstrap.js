// filepath: frontend/tests/e2e/bootstrap.js
/**
 * Shared bootstrap helpers for the C-01 E2E suite.
 *
 * Stubs the /api/v1/auth/login, /api/v1/bootstrap, and bootstrap snapshot
 * endpoints so the SPA can boot without a Django backend. Each test is
 * expected to call {@link installNetworkStubs} in `beforeEach`.
 */
export async function installNetworkStubs(page) {
  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session: "stub-session-token",
        user: { id: "user-1", role: "owner" },
      }),
    });
  });

  await page.route("**/api/v1/bootstrap", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        company: { id: "acme", name: "Acme", locale: "en" },
        currentUser: { id: "user-1", role: "owner" },
        branches: [],
      }),
    });
  });

  await page.route("**/api/v1/notifications**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    });
  });
}
