import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { api } from "../../api/client";
import { createFallbackState, fetchBootstrap } from "../../api/bootstrap";
import { bootstrapSnapshot } from "../../design-system/tokens";
import { PeoplePage } from "./PeoplePage";
import i18n from "../../i18n";

vi.mock("../../api/client", () => ({ api: vi.fn() }));
vi.mock("../../api/bootstrap", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../api/bootstrap")>(),
  fetchBootstrap: vi.fn(async () => ({
    current_user: { id: "operator", is_authenticated: true, role: "owner" },
    installation: { setup_required: false }, company: null,
    branches: [], branch_scope: [], permissions: [], enabled_modules: [],
  })),
}));

const request = vi.mocked(api);
const branchId = "11111111-1111-4111-8111-111111111111";
const jobRoleId = "22222222-2222-4222-8222-222222222222";

beforeEach(() => {
  request.mockReset();
  vi.mocked(fetchBootstrap).mockClear();
});

test.each([
  { role: "owner" as const, configured: false },
  { role: "owner" as const, configured: true },
  { role: "monitor" as const, configured: true },
])("$role creates users with only the selected fields (configured: $configured)", async ({ role, configured }) => {
  request.mockImplementation(async (path) => {
    if (path === "/api/v1/auth/company/members") return { memberships: [] };
    if (path === "/api/v1/organizations/branches") return { branches: configured ? [{
      id: branchId, name: "Main", code: "main", timezone: "Asia/Riyadh", operational_day_cutoff: "03:00:00", active: true,
    }] : [] };
    if (path === "/api/v1/organizations/job-roles") return { roles: configured ? [{
      id: jobRoleId, name: "Cashier", code: "cashier", active: true,
    }] : [] };
    if (path === "/api/v1/auth/company/users") return { user: { id: "created-user" } };
    throw new Error(`Unexpected path: ${path}`);
  });
  const state = createFallbackState(bootstrapSnapshot);
  render(<PeoplePage bootstrap={state} activeRole={role} />);
  const button = await screen.findByRole("button", { name: "Create user" });
  fireEvent.change(screen.getByLabelText("Login ID", { exact: true }), { target: { value: "new-employee" } });
  fireEvent.change(screen.getByLabelText("Display name", { exact: true }), { target: { value: "New Employee" } });
  fireEvent.change(screen.getByLabelText("Password", { exact: true }), { target: { value: "Test!Password-2026" } });
  fireEvent.click(button);
  await waitFor(() => expect(request).toHaveBeenCalledWith("/api/v1/auth/company/users", {
    method: "POST",
    body: {
      login_id: "new-employee", display_name: "New Employee", password: "Test!Password-2026", role: "employee",
      ...(role === "monitor" ? { branch_id: branchId, job_role_id: jobRoleId } : {}),
    },
  }));
  await screen.findByText("Company user created.");
});

const mutations = [
  { button: "Create user", path: "/api/v1/auth/company/users", success: "user_created", failure: "user_create_failed" },
  { button: "Create branch", path: "/api/v1/organizations/branches", success: "branch_created", failure: "branch_create_failed" },
  { button: "Create job role", path: "/api/v1/organizations/job-roles", success: "job_role_created", failure: "job_role_create_failed" },
  { button: "Assign branch", path: "/api/v1/auth/company/branch-memberships", success: "branch_assigned", failure: "branch_assignment_failed" },
];

test.each(mutations.flatMap((mutation) =>
  ["success", "lists_failed", "bootstrap_failed", "write_failed"].map((outcome) => ({ ...mutation, outcome })),
))("$button distinguishes write outcome from refresh ($outcome)", async ({ button, path, success, failure, outcome }) => {
  let writeSucceeded = false;
  request.mockImplementation(async (requestedPath, options) => {
    if (options?.method === "POST") {
      expect(requestedPath).toBe(path);
      if (outcome === "write_failed") throw new Error("Write rejected");
      writeSucceeded = true;
      return {};
    }
    if (writeSucceeded && outcome === "lists_failed") throw new Error("Refresh unavailable");
    if (requestedPath === "/api/v1/auth/company/members") return { memberships: [{
      user_id: "33333333-3333-4333-8333-333333333333", display_name: "Employee", role: "employee", active: true,
    }] };
    if (requestedPath === "/api/v1/organizations/branches") return { branches: [{
      id: branchId, name: "Main", code: "main", timezone: "Asia/Riyadh", operational_day_cutoff: "03:00:00", active: true,
    }] };
    if (requestedPath === "/api/v1/organizations/job-roles") return { roles: [{
      id: jobRoleId, name: "Cashier", code: "cashier", active: true,
    }] };
    throw new Error(`Unexpected path: ${requestedPath}`);
  });
  if (outcome === "bootstrap_failed") vi.mocked(fetchBootstrap).mockRejectedValueOnce(new Error("Bootstrap unavailable"));
  render(<PeoplePage bootstrap={createFallbackState(bootstrapSnapshot)} activeRole="owner" />);
  const submit = await screen.findByRole("button", { name: button });
  const form = submit.closest("form");
  if (!form) throw new Error("Mutation form not found");
  for (const input of form.querySelectorAll<HTMLInputElement>('input:not([type="time"])')) {
    fireEvent.change(input, { target: { value: "Example-2026!" } });
  }
  fireEvent.click(submit);
  if (outcome === "write_failed") {
    await screen.findByText(i18n.t(`people.${failure}`));
    expect(screen.queryByText(i18n.t(`people.${success}`), { exact: false })).toBeNull();
    expect(fetchBootstrap).not.toHaveBeenCalled();
  } else {
    const text = i18n.t(`people.${success}`) + (outcome === "success" ? "" : ` ${i18n.t("people.refresh_notice")}`);
    await screen.findByText(text);
    expect(screen.queryByText(i18n.t(`people.${failure}`))).toBeNull();
    expect(fetchBootstrap).toHaveBeenCalledTimes(1);
  }
  await waitFor(() => expect((submit as HTMLButtonElement).disabled).toBe(false));
  expect(request.mock.calls.filter(([, options]) => options?.method === "POST")).toHaveLength(1);
});
