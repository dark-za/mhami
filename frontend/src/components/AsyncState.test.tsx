/**
 * AsyncState tests for the FE-04 workflow surface.
 */
import { describe, expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { AsyncState } from "./AsyncState";

describe("AsyncState", () => {
  test("renders the error surface when an error is provided", () => {
    render(
      <AsyncState error="Boom!">
        <span>content</span>
      </AsyncState>,
    );
    const alert = screen.getByRole("alert");
    expect(alert.textContent ?? "").toContain("Boom!");
  });

  test("renders the loading surface when loading is true", () => {
    render(
      <AsyncState loading loadingLabel="Loading tasks…">
        <span>content</span>
      </AsyncState>,
    );
    const status = screen.getByRole("status");
    expect(status.textContent ?? "").toContain("Loading tasks…");
  });

  test("renders the empty surface when empty is true", () => {
    render(
      <AsyncState empty emptyMessage="No tasks yet.">
        <span>content</span>
      </AsyncState>,
    );
    const status = screen.getByRole("status");
    expect(status.textContent ?? "").toContain("No tasks yet.");
  });

  test("renders the children when not loading, errored, or empty", () => {
    render(
      <AsyncState>
        <span>rendered content</span>
      </AsyncState>,
    );
    expect(screen.getByText("rendered content")).toBeTruthy();
  });
});
