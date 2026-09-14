import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, expect, test, vi } from "vitest";
import { createFallbackState } from "../../api/bootstrap";
import { api } from "../../api/client";
import { bootstrapSnapshot } from "../../design-system/tokens";
import i18n from "../../i18n";
import { TasksPage } from "./TasksPage";

vi.mock("../../api/client", () => ({ api: vi.fn() }));

const request = vi.mocked(api);
const companyId = "99999999-9999-4999-8999-999999999999";
const branchId = "11111111-1111-4111-8111-111111111111";
const employeeId = "22222222-2222-4222-8222-222222222222";

beforeEach(async () => {
  request.mockReset();
  await i18n.changeLanguage("en");
});

function mockTaskRequests(outcome: "success" | "refresh_failed" | "write_failed") {
  let saved = false;
  request.mockImplementation(async (path, init) => {
    if (init?.method === "POST") {
      expect(path).toBe("/api/v1/tasks/instances/task-1/start");
      if (outcome === "write_failed") throw new Error("Write rejected");
      saved = true;
      return {};
    }
    if (path === "/api/v1/tasks/instances") {
      if (saved && outcome === "refresh_failed") throw new Error("Tasks unavailable");
      return {
        instances: [{
          id: "task-1",
          name: "Prepare opening checklist",
          status: saved ? "in_progress" : "pending",
          due_at: "2026-09-12T08:00:00Z",
          assigned_user_name: "Employee",
          branch_name: "Main",
          branch: "branch-1",
        }],
      };
    }
    if (path === "/api/v1/tasks/transfers") return { transfers: [] };
    if (path === "/api/v1/tasks/requests") return { requests: [] };
    if (path === "/api/v1/auth/company/members") return { memberships: [] };
    if (typeof path === "string" && path.startsWith("/api/v1/tasks/transfer-recipients")) {
      return { recipients: [] };
    }
    throw new Error(`Unexpected path: ${path}`);
  });
}

test.each(["success", "refresh_failed", "write_failed"] as const)(
  "task actions report the write result when follow-up refresh is %s",
  async (outcome) => {
    mockTaskRequests(outcome);
    render(
      <MemoryRouter>
        <TasksPage bootstrap={createFallbackState(bootstrapSnapshot)} />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: i18n.t("tasks.action.start") }));

    if (outcome === "write_failed") {
      await screen.findByText(i18n.t("tasks.action_failed", { action: i18n.t("tasks.action.start") }));
      expect(screen.queryByText(i18n.t("tasks.action_succeeded", { action: i18n.t("tasks.action.start") }), { exact: false })).toBeNull();
    } else {
      const success = i18n.t("tasks.action_succeeded", { action: i18n.t("tasks.action.start") });
      const message = success + (outcome === "refresh_failed" ? ` ${i18n.t("tasks.refresh_notice")}` : "");
      await screen.findByText(message);
      expect(screen.queryByText(i18n.t("tasks.action_failed", { action: i18n.t("tasks.action.start") }))).toBeNull();
    }

    await waitFor(() => expect(request.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1));
  },
);

test("creating a scheduled task uses the atomic backend endpoint", async () => {
  request.mockImplementation(async (path, init) => {
    if (init?.method === "POST") {
      expect(path).toBe("/api/v1/tasks/scheduled-tasks");
      return {
        template: { id: "template-1" },
        version: { id: "version-1" },
        schedule: { id: "schedule-1" },
      };
    }
    if (path === "/api/v1/tasks/instances") return { instances: [] };
    if (path === "/api/v1/tasks/transfers") return { transfers: [] };
    if (path === "/api/v1/tasks/requests") return { requests: [] };
    if (path === "/api/v1/auth/company/members") {
      return { memberships: [{ user_id: employeeId, display_name: "Employee", role: "employee", active: true }] };
    }
    throw new Error(`Unexpected path: ${path}`);
  });
  const fallback = createFallbackState(bootstrapSnapshot);
  const bootstrap = {
    ...fallback,
    branchScope: [{
      id: branchId,
      name: "Main",
      code: "main",
      timezone: "Asia/Riyadh",
      operational_day_cutoff: "03:00:00",
      active: true,
    }],
    snapshot: {
      ...fallback.snapshot,
      currentUser: {
        ...fallback.snapshot.currentUser,
        authenticated: true,
        role: "owner" as const,
      },
      company: { ...fallback.snapshot.company, id: companyId },
    },
  };

  render(
    <MemoryRouter>
      <TasksPage bootstrap={bootstrap} />
    </MemoryRouter>,
  );

  fireEvent.change(await screen.findByLabelText(i18n.t("tasks.name")), { target: { value: "Opening checklist" } });
  fireEvent.change(screen.getByLabelText(i18n.t("tasks.branch")), { target: { value: branchId } });
  fireEvent.change(screen.getByLabelText(i18n.t("tasks.employee")), { target: { value: employeeId } });
  fireEvent.change(screen.getByLabelText(i18n.t("tasks.instructions")), { target: { value: "Check counters." } });
  fireEvent.click(screen.getByRole("button", { name: i18n.t("tasks.create_task") }));

  await waitFor(() => expect(request.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1));
  expect(request.mock.calls.find(([, init]) => init?.method === "POST")?.[1]?.body).toMatchObject({
    branch_id: branchId,
    name: "Opening checklist",
    assigned_user_id: employeeId,
    instructions: "Check counters.",
    recurrence_type: "daily_fixed",
    scheduled_time: "09:00",
  });
  await screen.findByText(i18n.t("tasks.creation_success"));
});
