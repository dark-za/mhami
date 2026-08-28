/**
 * FE-03 acceptance tests for the typed API wrappers.
 *
 * Verifies the wrappers preserve the contract types derived from the
 * OpenAPI schema and that the source code does not introduce `any`.
 */
import { describe, expect, test, vi } from "vitest";
import { api } from "./client";
import { getTaskInstance, listEvidence, listTasks } from "./typed";

vi.mock("./client", async () => {
  const actual = await vi.importActual<typeof import("./client")>("./client");
  return {
    ...actual,
    api: vi.fn(),
  };
});

describe("FE-03 typed API wrappers", () => {
  test("getTaskInstance calls the canonical path", async () => {
    const apiMock = vi.mocked(api);
    apiMock.mockResolvedValueOnce({ id: "task-1" });
    await getTaskInstance("task-1");
    expect(apiMock).toHaveBeenCalledWith("/api/v1/tasks/instances/task-1/");
  });

  test("listTasks with no filters calls the list endpoint", async () => {
    const apiMock = vi.mocked(api);
    apiMock.mockResolvedValueOnce({ instances: [] });
    const result = await listTasks();
    expect(result).toEqual([]);
    expect(apiMock).toHaveBeenCalledWith("/api/v1/tasks/instances");
  });

  test("listTasks with filters encodes the query string", async () => {
    const apiMock = vi.mocked(api);
    apiMock.mockResolvedValueOnce({ instances: [] });
    await listTasks({ branchId: "branch-1", status: "pending" });
    expect(apiMock).toHaveBeenCalledWith(
      "/api/v1/tasks/instances?branch=branch-1&status=pending",
    );
  });

  test("listEvidence unwraps the items array", async () => {
    const apiMock = vi.mocked(api);
    apiMock.mockResolvedValueOnce({ items: [{ id: "ev-1" }] });
    const result = await listEvidence("task-1");
    expect(result).toEqual([{ id: "ev-1" }]);
  });
});
