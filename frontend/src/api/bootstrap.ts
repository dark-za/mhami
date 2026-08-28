import { ensureCsrfToken } from "./client";
import type { BootstrapSnapshot } from "../design-system/tokens";
import type { BootstrapApiResponse } from "./contract";

export type BootstrapState = {
  snapshot: BootstrapSnapshot;
  branches: BootstrapApiResponse["branches"];
  source: "live" | "fallback";
};

export function createFallbackState(snapshot: BootstrapSnapshot): BootstrapState {
  return {
    snapshot,
    branches: [],
    source: "fallback",
  };
}

export async function fetchBootstrap(): Promise<BootstrapApiResponse> {
  // C-04: hit the bootstrap endpoint with the credentials so the
  // csrftoken cookie is set, then capture the JSON response. The
  // request is idempotent and safe to call on every mount.
  await ensureCsrfToken();
  const response = await fetch("/api/v1/bootstrap", {
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Bootstrap request failed with ${response.status}`);
  }

  return (await response.json()) as BootstrapApiResponse;
}
