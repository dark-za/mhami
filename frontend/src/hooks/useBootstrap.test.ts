import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { createFallbackState, fetchBootstrap } from "../api/bootstrap";
import type { BootstrapApiResponse } from "../api/contract";
import { bootstrapSnapshot } from "../design-system/tokens";
import { useBootstrap } from "./useBootstrap";
import { SESSION_CHANGE_KEY, SESSION_RECHECK_EVENT } from "../api/session";

vi.mock("../api/bootstrap", async (importOriginal) => ({
  ...await importOriginal<typeof import("../api/bootstrap")>(),
  fetchBootstrap: vi.fn(),
}));

const fetchMock = vi.mocked(fetchBootstrap);

function response(id: string | null): BootstrapApiResponse {
  return {
    current_user: { id, login_id: id, display_name: id, is_authenticated: id !== null, role: id ? "owner" : null },
    company: id ? { id: "company", name: "Test Company", code: "test", status: "active", industry: "other" } : null,
    installation: { setup_required: false },
    permissions: [], branches: [], branch_scope: [], enabled_modules: [], feature_flags: [], app_version: "test",
  };
}

function deferred() {
  let resolve!: (value: BootstrapApiResponse) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<BootstrapApiResponse>((accept, fail) => { resolve = accept; reject = fail; });
  return { promise, resolve, reject };
}

function refresh(detail?: BootstrapApiResponse) {
  act(() => { window.dispatchEvent(new CustomEvent("mhami.bootstrap.refreshed", { detail })); });
}

beforeEach(() => { fetchMock.mockReset(); });

test("a late initial response cannot overwrite a newer login event", async () => {
  const initial = deferred();
  fetchMock.mockReturnValueOnce(initial.promise);
  const { result } = renderHook(useBootstrap);
  refresh(response("new-owner"));
  await act(async () => { initial.resolve(response(null)); });
  expect(result.current.state.snapshot.currentUser.id).toBe("new-owner");
  expect(result.current.state.snapshot.currentUser.authenticated).toBe(true);
  expect(result.current.loading).toBe(false);
});

test("a pending response cannot restore a logged-out session", async () => {
  const initial = deferred();
  fetchMock.mockReturnValueOnce(initial.promise);
  const { result } = renderHook(useBootstrap);
  act(() => { result.current.setState(createFallbackState(bootstrapSnapshot)); });
  await act(async () => { initial.resolve(response("old-owner")); });
  expect(result.current.state.source).toBe("fallback");
  expect(result.current.state.snapshot.currentUser.authenticated).toBe(false);
  expect(result.current.loading).toBe(false);
});

test("anonymous refresh discards the previous identity and organization", async () => {
  fetchMock.mockResolvedValueOnce(response("previous-owner"));
  const { result } = renderHook(useBootstrap);
  await waitFor(() => expect(result.current.state.snapshot.currentUser.id).toBe("previous-owner"));
  fetchMock.mockResolvedValueOnce(response(null));
  refresh();
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.state.snapshot.currentUser).toEqual(bootstrapSnapshot.currentUser);
  expect(result.current.state.snapshot.company).toEqual(bootstrapSnapshot.company);
  expect(result.current.state.source).toBe("live");
});

test.each([true, false])("latest reload wins regardless of completion order (old first: %s)", async (oldFirst) => {
  const old = deferred();
  const latest = deferred();
  fetchMock.mockReturnValueOnce(old.promise).mockReturnValueOnce(latest.promise);
  const { result } = renderHook(useBootstrap);
  refresh();
  expect(fetchMock).toHaveBeenCalledTimes(2);
  if (oldFirst) {
    await act(async () => { old.resolve(response("old-owner")); });
    expect(result.current.loading).toBe(true);
    expect(result.current.state.source).toBe("fallback");
  }
  await act(async () => { latest.resolve(response("latest-owner")); });
  if (!oldFirst) {
    await act(async () => { old.resolve(response("old-owner")); });
  }
  expect(result.current.state.snapshot.currentUser.id).toBe("latest-owner");
  expect(result.current.loading).toBe(false);
});

test("a failed refresh clears authenticated state", async () => {
  fetchMock.mockResolvedValueOnce(response("owner"));
  const { result } = renderHook(useBootstrap);
  await waitFor(() => expect(result.current.state.snapshot.currentUser.authenticated).toBe(true));
  const latest = deferred();
  fetchMock.mockReturnValueOnce(latest.promise);
  refresh();
  await act(async () => { latest.reject(new Error("offline")); });
  expect(result.current.error).toBe("bootstrap_failed");
  expect(result.current.state.source).toBe("fallback");
  expect(result.current.state.snapshot.currentUser.authenticated).toBe(false);
});

test("a superseded failure cannot clear a newer authenticated state", async () => {
  const initial = deferred();
  fetchMock.mockReturnValueOnce(initial.promise);
  const { result } = renderHook(useBootstrap);
  refresh(response("owner"));
  await act(async () => { initial.reject(new Error("old request failed")); });
  expect(result.current.error).toBeNull();
  expect(result.current.state.snapshot.currentUser.authenticated).toBe(true);
});

test.each(["storage", "rejected"])("%s session change hides old data and reloads from server", async (trigger) => {
  fetchMock.mockResolvedValueOnce(response("old-owner"));
  const { result } = renderHook(useBootstrap);
  await waitFor(() => expect(result.current.state.snapshot.currentUser.authenticated).toBe(true));
  const pending = deferred();
  fetchMock.mockReturnValueOnce(pending.promise);
  act(() => {
    window.dispatchEvent(trigger === "storage"
      ? new StorageEvent("storage", { key: SESSION_CHANGE_KEY, newValue: "untrusted-value" })
      : new Event(SESSION_RECHECK_EVENT));
  });
  expect(result.current.state.snapshot.currentUser.authenticated).toBe(false);
  expect(result.current.loading).toBe(true);
  await act(async () => { pending.resolve(response(null)); });
  expect(result.current.state.source).toBe("live");
  expect(result.current.state.snapshot.currentUser.authenticated).toBe(false);
  expect(result.current.loading).toBe(false);
});

test("unrelated storage changes do not refresh the session", async () => {
  fetchMock.mockResolvedValueOnce(response("owner"));
  renderHook(useBootstrap);
  await act(async () => {});
  act(() => { window.dispatchEvent(new StorageEvent("storage", { key: "mhami.locale", newValue: "ar" })); });
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("focus revalidates without hiding the workspace while the same session is pending", async () => {
  fetchMock.mockResolvedValueOnce(response("owner"));
  const { result } = renderHook(useBootstrap);
  await waitFor(() => expect(result.current.state.snapshot.currentUser.authenticated).toBe(true));
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
  const pending = deferred();
  fetchMock.mockReturnValueOnce(pending.promise);
  try {
    act(() => { window.dispatchEvent(new Event("focus")); document.dispatchEvent(new Event("visibilitychange")); });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(result.current.loading).toBe(false);
    expect(result.current.state.snapshot.currentUser.id).toBe("owner");
    await act(async () => { pending.resolve(response(null)); });
    expect(result.current.state.snapshot.currentUser.authenticated).toBe(false);
  } finally {
    vi.restoreAllMocks();
  }
});
