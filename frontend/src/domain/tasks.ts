/** Task instance and transfer payloads.
 *
 * ``TaskInstance`` (raw) is sourced from the OpenAPI schema; ``TaskSummary``
 * adds the human-readable ``name`` that the backend does not return directly
 * (it is resolved client-side by joining with the template name when
 * available — this is a convenience for the shell while the platform keeps
 * the source schema strict).
 */

import type { components } from "../api/generated-types";

export type TaskInstance = components["schemas"]["TaskInstance"];

export interface TaskSummary
  extends Pick<TaskInstance, "id" | "status" | "due_at" | "assigned_user" | "branch"> {
  name: string;
}

export type TaskTransferRequest = components["schemas"]["TaskTransferRequest"];

export interface TaskTransferSummary {
  id: string;
  task_instance: string;
  requested_by: string;
  requested_to: string;
  status: string;
  reason: string;
}
