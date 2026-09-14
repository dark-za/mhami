import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { api } from "../../api/client";
import i18n from "../../i18n";
import { ReviewsPage } from "./ReviewsPage";

vi.mock("../../api/client", () => ({ api: vi.fn() }));

const request = vi.mocked(api);

beforeEach(async () => {
  request.mockReset();
  await i18n.changeLanguage("en");
});

function mockReviewRequests(outcome: "success" | "refresh_failed" | "write_failed") {
  let saved = false;
  request.mockImplementation(async (path, init) => {
    if (init?.method === "POST") {
      expect(path).toBe("/api/v1/reviews/decisions");
      if (outcome === "write_failed") throw new Error("Write rejected");
      saved = true;
      return {};
    }
    if (path === "/api/v1/reviews/dashboard") {
      if (saved && outcome === "refresh_failed") throw new Error("Dashboard unavailable");
      return { summary: { completed_today: 0, overdue: 0, quality_exceptions: 0 }, branches: [] };
    }
    if (path === "/api/v1/reviews/queue") {
      return {
        items: saved ? [] : [{
          id: "review-item",
          kind: "evidence",
          title: "Check opening photo",
          branch_name: "Main",
          status: "pending",
          reason: "Needs approval",
          task_instance_id: null,
          evidence_item_id: "evidence-item",
          issue_report_id: null,
        }],
      };
    }
    if (path === "/api/v1/reviews/policy") {
      return {
        employee_score_visibility: "summary",
        historical_report_restatement: false,
        monitor_approval_required: true,
        sensitive_task_claim_restricted: true,
        extra_evidence_required: false,
        owner_alerts_enabled: true,
        approved_task_weight_cap: 5,
      };
    }
    throw new Error(`Unexpected path: ${path}`);
  });
}

test.each(["success", "refresh_failed", "write_failed"] as const)(
  "review decisions report the write result when follow-up refresh is %s",
  async (outcome) => {
    mockReviewRequests(outcome);
    render(<ReviewsPage activeRole="monitor" />);

    fireEvent.click(await screen.findByRole("button", { name: i18n.t("reviews.approve") }));

    if (outcome === "write_failed") {
      await screen.findByText(i18n.t("reviews.decision_failed"));
      expect(screen.queryByText(i18n.t("reviews.decision_saved"), { exact: false })).toBeNull();
    } else {
      const message = i18n.t("reviews.decision_saved") +
        (outcome === "refresh_failed" ? ` ${i18n.t("reviews.refresh_notice")}` : "");
      await screen.findByText(message);
      expect(screen.queryByText(i18n.t("reviews.decision_failed"))).toBeNull();
    }

    await waitFor(() => expect(request.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1));
  },
);
