/**
 * ExportsPage — defect 2: export status/type labels use locale keys with fallback.
 */
import { describe, expect, test, beforeEach, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import i18n from "../../i18n";

const policyMock = {
  id: "policy-1",
  future_notification_boundaries: ["emails"],
  external_storage_boundaries: [],
  provider_review_checklist: [],
};

const requestsMock = (status: string, exportType: string) => ({
  requests: [
    {
      id: "req-1",
      export_type: exportType,
      branch_ids: [],
      categories: ["tasks"],
      status,
      download_token: "tok",
      file_name: "file.csv",
      expires_at: "2099-01-01T00:00:00Z",
    },
  ],
});

vi.mock("../../api/client", () => ({
  api: vi.fn(),
}));

import { api } from "../../api/client";
import { ExportsPage } from "./ExportsPage";

const mockedApi = api as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  await act(async () => {
    await i18n.changeLanguage("en");
  });
});

describe("ExportsPage localization", () => {
  test("translates export status and type via locale keys (EN)", async () => {
    mockedApi.mockImplementation(async (path: string) => {
      if (path === "/api/v1/exports/policy") return policyMock as never;
      if (path === "/api/v1/exports/requests/list") return requestsMock("queued", "csv") as never;
      throw new Error(`unexpected ${path}`);
    });
    await act(async () => {
      render(<ExportsPage />);
    });
    await waitFor(() => {
      expect(screen.getByText("Queued")).toBeTruthy();
      expect(screen.getAllByText("CSV").length).toBeGreaterThan(0);
    });
    // Raw API values should not appear when translation exists
    expect(screen.queryByText("queued")).toBeNull();
  });

  test("translates export status and type via locale keys (AR)", async () => {
    await act(async () => {
      await i18n.changeLanguage("ar");
    });
    mockedApi.mockImplementation(async (path: string) => {
      if (path === "/api/v1/exports/policy") return policyMock as never;
      if (path === "/api/v1/exports/requests/list") return requestsMock("completed", "pdf") as never;
      throw new Error(`unexpected ${path}`);
    });
    await act(async () => {
      render(<ExportsPage />);
    });
    await waitFor(() => {
      expect(screen.getByText("مكتملة")).toBeTruthy();
      expect(screen.getAllByText("PDF").length).toBeGreaterThan(0);
    });
  });

  test("falls back to API value for unknown export status/type", async () => {
    mockedApi.mockImplementation(async (path: string) => {
      if (path === "/api/v1/exports/policy") return policyMock as never;
      if (path === "/api/v1/exports/requests/list") return requestsMock("mystery_status", "xlsx") as never;
      throw new Error(`unexpected ${path}`);
    });
    await act(async () => {
      render(<ExportsPage />);
    });
    await waitFor(() => {
      expect(screen.getByText("mystery_status")).toBeTruthy();
      expect(screen.getByText("XLSX")).toBeTruthy();
    });
  });
});
