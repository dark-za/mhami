/**
 * AIControlPage — defect 2: connector health/status values use locale keys with fallback.
 */
import { describe, expect, test, beforeEach, vi } from "vitest";
import { act, render, waitFor } from "@testing-library/react";
import i18n from "../../i18n";

vi.mock("../../api/client", () => ({
  api: vi.fn(),
}));

import { api } from "../../api/client";
import { AIControlPage } from "./AIControlPage";

const mockedApi = api as unknown as ReturnType<typeof vi.fn>;

const providerMock = {
  provider_name: "fake",
  endpoint_url: "",
  model_name: "test-model",
  credential_reference: "",
  monthly_token_limit: 10000,
  monthly_cost_limit: "0.00",
  enabled: true,
};

function connectorMock(status: string, health: string) {
  return {
    enrollment: {
      id: "c-1",
      connector_version: "1.0.0",
      compatibility_window: ">=0.1,<1.0",
      status,
      health_status: health,
      last_seen_at: null,
      revoked_at: null,
      shared_secret_fingerprint: "",
    },
  };
}

beforeEach(async () => {
  vi.clearAllMocks();
  await act(async () => {
    await i18n.changeLanguage("en");
  });
});

describe("AIControlPage connector localization", () => {
  test("translates connector health and status (EN)", async () => {
    mockedApi.mockImplementation(async (path: string) => {
      if (path === "/api/v1/ai/provider") return providerMock as never;
      if (path === "/api/v1/connectors/enrollment") return connectorMock("active", "healthy") as never;
      throw new Error(`unexpected ${path}`);
    });
    await act(async () => {
      render(<AIControlPage />);
    });
    await waitFor(() => {
      expect(document.body.textContent ?? "").toContain("Healthy");
      expect(document.body.textContent ?? "").toContain("Active");
    });
  });

  test("translates connector health and status (AR)", async () => {
    await act(async () => {
      await i18n.changeLanguage("ar");
    });
    mockedApi.mockImplementation(async (path: string) => {
      if (path === "/api/v1/ai/provider") return providerMock as never;
      if (path === "/api/v1/connectors/enrollment") return connectorMock("revoked", "degraded") as never;
      throw new Error(`unexpected ${path}`);
    });
    await act(async () => {
      render(<AIControlPage />);
    });
    await waitFor(() => {
      expect(document.body.textContent ?? "").toContain("متدهور");
      expect(document.body.textContent ?? "").toContain("ملغى");
    });
  });

  test("falls back to API value for unknown connector status/health", async () => {
    mockedApi.mockImplementation(async (path: string) => {
      if (path === "/api/v1/ai/provider") return providerMock as never;
      if (path === "/api/v1/connectors/enrollment") return connectorMock("mystery_status", "mystery_health") as never;
      throw new Error(`unexpected ${path}`);
    });
    await act(async () => {
      render(<AIControlPage />);
    });
    await waitFor(() => {
      expect(document.body.textContent ?? "").toContain("mystery_status");
      expect(document.body.textContent ?? "").toContain("mystery_health");
    });
  });

  test("shows offline/pending defaults when connector is null", async () => {
    mockedApi.mockImplementation(async (path: string) => {
      if (path === "/api/v1/ai/provider") return providerMock as never;
      if (path === "/api/v1/connectors/enrollment") return { enrollment: null } as never;
      throw new Error(`unexpected ${path}`);
    });
    await act(async () => {
      render(<AIControlPage />);
    });
    await waitFor(() => {
      // No connector => offline / pending locale keys
      expect(document.body.textContent ?? "").toMatch(/offline|غير متصل/i);
    });
  });
});
