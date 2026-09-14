/** Task instance and transfer payloads.
 *
 * ``TaskInstance`` is sourced from the OpenAPI schema. ``TaskSummary`` keeps
 * the task-card payload explicit while preserving the human-readable name
 * supplied by the backend.
 */

import type { components } from "../api/generated-types";

export type TaskInstance = components["schemas"]["TaskInstance"];

export interface TaskSummary
  extends Pick<
    TaskInstance,
    "id" | "status" | "due_at" | "assigned_user" | "assigned_user_name" | "branch" | "branch_name" | "name"
  > {}

export type TaskTransferRequest = components["schemas"]["TaskTransferRequest"];

export interface TaskTransferSummary {
  id: string;
  task_name?: string;
  task_instance: string;
  requested_by: string;
  requested_by_name?: string;
  requested_to: string;
  requested_to_name?: string;
  status: string;
  reason: string;
}
