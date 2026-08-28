/** Pilot program, dashboard, reports, issues, and change request payloads. */

import type { components } from "../api/generated-types";

export type PilotProgram = components["schemas"]["PilotProgram"];
export type PilotIssue = components["schemas"]["PilotIssue"];
export type PilotChangeRequest = components["schemas"]["PilotChangeRequest"];
export type PilotWeeklyReport = components["schemas"]["PilotWeeklyReport"];
export type PilotDashboard = components["schemas"]["PilotDashboard"];

/** Convenience aliases that tighten the OpenAPI ``unknown`` fields into the
 * concrete shapes the shell renders. They cast at the boundary so the rest
 * of the application sees stable types. */
export interface PilotProgramView
  extends Omit<PilotProgram, "success_measures" | "escalation_contacts" | "operating_checklist" | "weekly_metrics_goal"> {
  success_measures: string[];
  escalation_contacts: string[];
  operating_checklist: string[];
  weekly_metrics_goal: Record<string, unknown>;
}

export interface PilotReportView
  extends Omit<PilotWeeklyReport, "metrics" | "ai_agreement_rate"> {
  metrics: Record<string, unknown>;
  ai_agreement_rate: string | number;
}
