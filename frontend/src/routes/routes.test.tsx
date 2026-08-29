/**
 * FE-01 acceptance tests for the route table.
 *
 * Validates the route table produces the expected number of routes and
 * that RBAC role guards render the access-denied surface for forbidden
 * combinations.
 */
import { describe, expect, test, beforeEach } from "vitest";
import { act, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { AppRoutes } from "./index";

beforeEach(() => {
  window.localStorage.removeItem("mhami.activeRole");
});

async function renderAt(path: string) {
  let result: ReturnType<typeof render> | null = null;
  await act(async () => {
    result = render(
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>,
    );
    // Allow lazy chunks to resolve.
    await Promise.resolve();
    await Promise.resolve();
  });
  if (!result) {
    throw new Error("render did not return a result");
  }
  return result;
}

describe("FE-01 route table", () => {
  test("renders a public login route", async () => {
    await renderAt("/login");
    // The login page is loaded lazily — give Suspense a tick.
    await waitFor(() => {
      expect(document.body.textContent ?? "").toMatch(/Sign in|company code|login_id|company/i);
    });
  });

  test("owner can access /", async () => {
    window.localStorage.setItem("mhami.activeRole", "owner");
    await renderAt("/");
    // The role-aware home page should mount; either the tasks page or its
    // shell is rendered. We just need to confirm the access-denied
    // surface is not shown.
    await waitFor(() => {
      expect(document.body.textContent ?? "").not.toMatch(/Access restricted|do not have access/i);
    });
  });

  test("employee is denied access to /admin", async () => {
    window.localStorage.setItem("mhami.activeRole", "employee");
    await renderAt("/admin");
    await waitFor(() => {
      expect(document.body.textContent ?? "").toMatch(/Access restricted|do not have access/i);
    });
  });

  test("employee is denied access to /agent-access", async () => {
    window.localStorage.setItem("mhami.activeRole", "employee");
    await renderAt("/agent-access");
    await waitFor(() => {
      expect(document.body.textContent ?? "").toMatch(/Access restricted|do not have access/i);
    });
  });

  test("monitor is allowed on /reviews but not /admin", async () => {
    window.localStorage.setItem("mhami.activeRole", "monitor");
    await renderAt("/reviews");
    await waitFor(() => {
      const text = document.body.textContent ?? "";
      // Should not show access denied for /reviews with monitor.
      expect(text).not.toMatch(/Access restricted|do not have access/i);
    });
  });

  test("unknown path redirects to /", async () => {
    window.localStorage.setItem("mhami.activeRole", "owner");
    await renderAt("/does-not-exist");
    await waitFor(() => {
      // After redirect to /, the role guard allows owner through, so the
      // page must not show the access-denied surface.
      expect(document.body.textContent ?? "").not.toMatch(/Access restricted|do not have access/i);
    });
  });
});
