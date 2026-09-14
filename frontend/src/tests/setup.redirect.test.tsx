import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { MemoryRouter, useLocation } from "react-router";
import { createFallbackState } from "../api/bootstrap";
import { bootstrapSnapshot } from "../design-system/tokens";
import { AppRoutes } from "../routes";

vi.mock("../pages/DashboardPage", () => ({ default: () => <div>Owner dashboard</div> }));
vi.mock("../pages/tasks/TasksPage", () => ({ default: () => <div>Employee tasks</div> }));

function Location() {
  return <output data-testid="location">{useLocation().pathname}</output>;
}

test.each(["owner", "monitor", "employee"] as const)(
  "an authenticated %s leaving setup reaches their default page",
  async (role) => {
    const state = createFallbackState(bootstrapSnapshot);
    state.source = "live";
    state.setupRequired = false;
    state.snapshot.currentUser = { ...state.snapshot.currentUser, authenticated: true, role };
    render(<MemoryRouter initialEntries={["/setup"]}><AppRoutes bootstrap={state} /><Location /></MemoryRouter>);
    await screen.findByText(role === "employee" ? "Employee tasks" : "Owner dashboard");
    expect(screen.getByTestId("location").textContent).toBe(role === "employee" ? "/tasks" : "/dashboard");
  },
);
