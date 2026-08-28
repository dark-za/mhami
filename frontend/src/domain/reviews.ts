/** Review queue, policy, and dashboard payloads.
 *
 * ``ReviewPolicy`` comes from the OpenAPI schema. ``ReviewQueueItem`` and
 * ``ReviewDashboard`` are kept as hand-written shapes because spectacular
 * does not annotate the dashboard/queue responses (they are returned via
 * ``Response({"items": [...]})`` style payloads without explicit
 * ``@extend_schema(responses=...)`` decorations).
 */

import type { components } from "../api/generated-types";

export type ReviewPolicy = components["schemas"]["ReviewPolicy"];
export type ReviewDecision = components["schemas"]["ReviewDecision"];
export type ReviewDecisionCreate = components["schemas"]["ReviewDecisionCreate"];

export type ReviewQueueItemKind = "task" | "evidence" | "issue";

export interface ReviewQueueItem {
  kind: ReviewQueueItemKind;
  id: string;
  branch_id: string;
  branch_name: string;
  title: string;
  status: string;
  reason: string;
  created_at: string;
  task_instance_id?: string;
  evidence_item_id?: string;
  issue_report_id?: string;
}

export interface ReviewDashboardCompany {
  id: string;
  name: string;
  code: string;
  status: string;
  trial_days_left: number;
}

export interface ReviewDashboardSummary {
  completed_today: number;
  overdue: number;
  quality_exceptions: number;
  open_issues: number;
  pending_review: number;
}

export interface ReviewDashboardBranch {
  branch_id: string;
  branch_name: string;
  completed_today: number;
  overdue: number;
  quality_exceptions: number;
}

export interface ReviewDashboard {
  company: ReviewDashboardCompany;
  summary: ReviewDashboardSummary;
  branches: ReviewDashboardBranch[];
}
