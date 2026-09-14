import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { api } from "../../api/client";
import type { AgentGrant } from "../../domain";
import i18n from "../../i18n";
import { AgentAccessPage } from "./AgentAccessPage";

vi.mock("../../api/client", () => ({ api: vi.fn() }));
const request = vi.mocked(api);
const fakeSecret = "test-only-one-time-secret";
const grant: AgentGrant = {
  id: "existing-grant", company: "company", user: "owner",
  client_name: "Test client", client_fingerprint: `sha256:${"0".repeat(64)}`,
  scopes: ["read:tasks"], status: "active", active: true,
  expires_at: "2099-01-01T00:00:00Z", revoked_at: null,
  created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z",
};

beforeEach(() => { request.mockReset(); });

function mockRequests(action: "create" | "revoke", outcome: string, pendingRefresh?: Promise<unknown>) {
  let saved = false;
  request.mockImplementation(async (path, init) => {
    if (init?.method === "POST") {
      expect(path).toBe(action === "create" ? "/api/v1/agent/grants" : `/api/v1/agent/grants/${grant.id}/revoke`);
      if (outcome === "write_failed") throw new Error("Write rejected");
      saved = true;
      return action === "create" ? { ...grant, id: "new-grant", secret: fakeSecret } : { ...grant, active: false, status: "revoked" };
    }
    if (path === "/api/v1/agent/grants") {
      if (saved && pendingRefresh) return pendingRefresh;
      if (saved && outcome === "refresh_failed") throw new Error("List unavailable");
      return { grants: [{ ...grant, active: !(saved && action === "revoke"), status: saved && action === "revoke" ? "revoked" : "active" }] };
    }
    if (path === "/api/v1/agent/scopes") return { scopes: [{ value: "read:tasks", status: "enabled" }] };
    if (path === "/api/v1/agent/logs") return { logs: [] };
    if (path === "/api/v1/auth/company/members") return { memberships: [{ user_id: "owner", display_name: "Test owner", role: "owner", active: true }] };
    throw new Error(`Unexpected path: ${path}`);
  });
}

test.each((["create", "revoke"] as const).flatMap((action) =>
  ["success", "refresh_failed", "write_failed"].map((outcome) => ({ action, outcome })),
))("$action reports the actual write result ($outcome)", async ({ action, outcome }) => {
  mockRequests(action, outcome);
  render(<AgentAccessPage />);
  const button = await screen.findByRole("button", { name: i18n.t(`agent_access.${action === "create" ? "create_grant" : "revoke"}`) });
  fireEvent.click(button);
  const successKey = `agent_access.${action === "create" ? "grant_created" : "grant_revoked"}`;
  const errorKey = `agent_access.${action === "create" ? "create_failed" : "revoke_failed"}`;
  if (outcome === "write_failed") {
    await screen.findByText(i18n.t(errorKey));
    expect(screen.queryByText(i18n.t(successKey), { exact: false })).toBeNull();
    expect(screen.queryByLabelText(i18n.t("agent_access.secret_title"))).toBeNull();
  } else {
    const message = i18n.t(successKey) + (outcome === "refresh_failed" ? ` ${i18n.t("agent_access.refresh_notice")}` : "");
    await screen.findByText(message);
    expect(screen.queryByText(i18n.t(errorKey))).toBeNull();
    if (action === "create") {
      expect((screen.getByLabelText(i18n.t("agent_access.secret_title")) as HTMLInputElement).value).toBe(fakeSecret);
    }
  }
  const posts = request.mock.calls.filter(([, init]) => init?.method === "POST");
  expect(posts).toHaveLength(1);
  if (action === "create") expect(posts[0][1]?.body).toMatchObject({ user_id: "owner", scopes: ["read:tasks"] });
});

test("the one-time secret is visible before follow-up GETs finish and survives their failure", async () => {
  let rejectRefresh!: (error: Error) => void;
  const pendingRefresh = new Promise<unknown>((_resolve, reject) => { rejectRefresh = reject; });
  mockRequests("create", "success", pendingRefresh);
  render(<AgentAccessPage />);
  const button = await screen.findByRole("button", { name: i18n.t("agent_access.create_grant") });
  fireEvent.click(button);
  const secretField = await screen.findByLabelText(i18n.t("agent_access.secret_title"));
  expect((secretField as HTMLInputElement).value).toBe(fakeSecret);
  expect((button as HTMLButtonElement).disabled).toBe(true);
  expect(request.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
  await act(async () => rejectRefresh(new Error("Refresh interrupted")));
  await screen.findByText(`${i18n.t("agent_access.grant_created")} ${i18n.t("agent_access.refresh_notice")}`);
  await waitFor(() => expect((button as HTMLButtonElement).disabled).toBe(false));
  expect((secretField as HTMLInputElement).value).toBe(fakeSecret);
  expect(request.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
});
