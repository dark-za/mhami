/**
 * FE-05 acceptance tests for the CSRF-aware fetch wrapper.
 */
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { api, ensureCsrfToken, getCsrfToken, ApiError } from "./client";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  document.cookie = "csrftoken=; path=/";
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("FE-05 CSRF integration", () => {
  test("getCsrfToken reads the cookie value", () => {
    document.cookie = "csrftoken=abc123; path=/";
    expect(getCsrfToken()).toBe("abc123");
  });

  test("ensureCsrfToken hits the bootstrap endpoint and stops early if cookie exists", async () => {
    document.cookie = "csrftoken=present; path=/";
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 200 }));
    await ensureCsrfToken();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  test("ensureCsrfToken issues a GET to /api/v1/bootstrap when cookie is missing", async () => {
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    document.cookie = "other=1; path=/";
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 200 }));
    await ensureCsrfToken();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/bootstrap",
      expect.objectContaining({ method: "GET", credentials: "include" }),
    );
  });

  test("api() adds the X-CSRFToken header to POST requests", async () => {
    document.cookie = "csrftoken=csrf-secret; path=/";
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 200, headers: { "content-type": "application/json" } }));
    await api("/api/v1/auth/login", {
      method: "POST",
      body: { login_id: "u" },
    });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers["X-CSRFToken"]).toBe("csrf-secret");
  });

  test("api() does NOT add the X-CSRFToken header to GET requests", async () => {
    document.cookie = "csrftoken=csrf-secret; path=/";
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 200, headers: { "content-type": "application/json" } }));
    await api("/api/v1/bootstrap");
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers["X-CSRFToken"]).toBeUndefined();
  });

  test("api() throws an ApiError on a 4xx response", async () => {
    document.cookie = "csrftoken=csrf-secret; path=/";
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Invalid" }), {
        status: 400,
        headers: { "content-type": "application/json" },
      }),
    );
    await expect(api("/api/v1/auth/login", { method: "POST", body: {} })).rejects.toBeInstanceOf(ApiError);
  });

  test("api() sends credentials: include for cookie-bound sessions", async () => {
    document.cookie = "csrftoken=csrf-secret; path=/";
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 200 }));
    await api("/api/v1/bootstrap");
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.credentials).toBe("include");
  });
});
