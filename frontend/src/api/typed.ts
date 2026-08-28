/**
 * Type-safe wrappers around the shared `api()` helper. Each wrapper
 * resolves to a strongly-typed payload derived from the OpenAPI schema
 * (`generated-types.ts`). Pages should prefer these helpers over inline
 * `api<T>(...)` calls so the contract is enforced at the type level.
 */
import type { components } from "./generated-types";
import { api } from "./client";

type Schemas = components["schemas"];

export type Company = Schemas["BootstrapCompany"];
export type TaskInstance = Schemas["TaskInstance"];
export type EvidenceItem = Schemas["EvidenceItem"];

/**
 * Fetch a task instance. The response type is derived from the OpenAPI
 * operation so the wrapper stays in sync with the backend contract.
 */
export async function getTaskInstance(taskId: string): Promise<TaskInstance> {
  return api(`/api/v1/tasks/instances/${taskId}/`);
}

export interface ListTasksFilters {
  branchId?: string;
  status?: string;
}

export async function listTasks(filters: ListTasksFilters = {}): Promise<TaskInstance[]> {
  const search = new URLSearchParams();
  if (filters.branchId) {
    search.set("branch", filters.branchId);
  }
  if (filters.status) {
    search.set("status", filters.status);
  }
  const suffix = search.toString();
  const path = suffix ? `/api/v1/tasks/instances?${suffix}` : "/api/v1/tasks/instances";
  const payload = await api<{ instances?: TaskInstance[] }>(path);
  return payload.instances ?? [];
}

export async function listEvidence(taskId: string): Promise<EvidenceItem[]> {
  const payload = await api<{ items?: EvidenceItem[] }>(`/api/v1/evidence/?task=${taskId}`);
  return payload.items ?? [];
}
