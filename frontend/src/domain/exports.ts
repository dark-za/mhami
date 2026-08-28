/** Export policy and request payloads.
 *
 * ``categories`` and ``branch_ids`` are stored as JSONField on the backend
 * and spectacular renders them as ``unknown``; the shell views the values
 * as string arrays. The boundary types here tighten those fields so the
 * page components do not need their own casts.
 */

import type { components } from "../api/generated-types";

export type ExportBoundaryPolicy = components["schemas"]["ExportBoundaryPolicy"];
export type ExportRequest = components["schemas"]["ExportRequest"];
export type ExportRequestCreate = components["schemas"]["ExportRequestCreate"];

export interface ExportPolicy {
  id: string;
  future_notification_boundaries: string[];
  external_storage_boundaries: string[];
  provider_review_checklist: string[];
}

export interface ExportRequestItem {
  id: string;
  export_type: string;
  branch_ids: string[];
  categories: string[];
  status: string;
  download_token: string;
  file_name: string;
  expires_at: string;
  completed_at?: string | null;
  downloaded_at?: string | null;
}
