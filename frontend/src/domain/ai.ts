/** AI provider, criteria, and shadow summary payloads.
 *
 * ``AIProviderConfig`` and ``AIAnalysisCriterion`` map 1:1 to the OpenAPI
 * schemas. ``AIShadowSummary`` is hand-written because the
 * ``/api/v1/ai/shadow`` endpoint does not declare a response schema in
 * spectacular.
 */

import type { components } from "../api/generated-types";

export type AIProviderConfig = components["schemas"]["AIProviderConfig"];
export type AIAnalysisCriterion = components["schemas"]["AIAnalysisCriterion"];
export type AIAnalysisCriterionCreate = components["schemas"]["AIAnalysisCriterionCreate"];

export interface AICriterionSummary
  extends Pick<AIAnalysisCriterion, "id" | "version_number" | "title" | "shadow_mode" | "auto_pass_enabled" | "auto_pass_risk_threshold" | "active" | "created_at"> {}

export interface AIShadowSummaryCompany {
  id: string;
  name: string;
  code: string;
}

export interface AIShadowSummaryStats {
  total_runs: number;
  completed: number;
  needs_review: number;
  agreement_rate: number;
}

export interface AIShadowSummaryRun {
  id: string;
  evidence_item_id?: string | null;
  status: string;
  risk_level: string;
  shadow_mode: boolean;
  auto_pass_eligible: boolean;
  auto_pass_activated: boolean;
  created_at: string;
}

export interface AIShadowSummary {
  company: AIShadowSummaryCompany;
  summary: AIShadowSummaryStats;
  runs: AIShadowSummaryRun[];
}
