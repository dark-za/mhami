import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { api } from "../api/client";
import { useNotifications } from "./useNotifications";

vi.mock("../api/client", () => ({ api: vi.fn() }));
const request = vi.mocked(api);

beforeEach(() => {
  request.mockReset();
});

test("does not request notifications before authentication and loads after login", async () => {
  request.mockResolvedValue({ notifications: [] });
  const { result, rerender } = renderHook(({ session }) => useNotifications(session), {
    initialProps: { session: null as string | null },
  });
  expect(request).not.toHaveBeenCalled();
  rerender({ session: "company:owner" });
  await waitFor(() => expect(result.current.items).toEqual([]));
  expect(request).toHaveBeenCalledTimes(1);
  rerender({ session: null });
  expect(result.current).toEqual({ items: null, error: false });
});

test("ignores a previous account's response after an account switch", async () => {
  let finishOld!: (value: unknown) => void;
  request.mockImplementationOnce(() => new Promise(resolve => { finishOld = resolve; }));
  request.mockResolvedValueOnce({ notifications: [] });
  const { result, rerender } = renderHook(({ session }) => useNotifications(session), {
    initialProps: { session: "company:old-user" },
  });
  const oldSignal = request.mock.calls[0][1]?.signal;
  rerender({ session: "company:new-user" });
  expect(oldSignal?.aborted).toBe(true);
  await waitFor(() => expect(result.current.items).toEqual([]));
  await act(async () => finishOld({ notifications: [{ id: "private-old-notification" }] }));
  expect(result.current.items).toEqual([]);
});

test("clears a request error when signing out", async () => {
  request.mockRejectedValue(new Error("network unavailable"));
  const { result, rerender } = renderHook(({ session }) => useNotifications(session), {
    initialProps: { session: "company:owner" as string | null },
  });
  await waitFor(() => expect(result.current.error).toBe(true));
  rerender({ session: null });
  expect(result.current).toEqual({ items: null, error: false });
});
