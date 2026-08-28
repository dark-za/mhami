/** Evidence capture / issue / discussion payloads.
 *
 * Single-item shapes come from the OpenAPI schema. The summary interfaces
 * project the subset the shell renders and lift the optional fields to
 * required so component code does not have to defend against ``undefined``.
 */

import type { components } from "../api/generated-types";

export type EvidenceItem = components["schemas"]["EvidenceItem"];
export type EvidenceIssueReport = components["schemas"]["TaskIssueReport"];
export type EvidenceMessage = components["schemas"]["TaskDiscussionMessage"];

export interface EvidenceSummary {
  id: string;
  evidence_type: string;
  duplicate_risk_score: number;
  face_detected: boolean;
  created_at: string;
  private_media_name?: string;
  note_text?: string;
}

export interface EvidenceIssueSummary {
  id: string;
  note: string;
  created_at: string;
}

export interface EvidenceMessageSummary {
  id: string;
  message: string;
  created_at: string;
}
