import { api } from "./client";
import type { BootstrapSnapshot } from "../design-system/tokens";
import type { BootstrapApiResponse } from "./contract";

export type BootstrapState = {
  snapshot: BootstrapSnapshot;
  branches: BootstrapApiResponse["branches"];
  branchScope: BootstrapApiResponse["branch_scope"];
  setupRequired: boolean;
  source: "live" | "fallback";
};

export function createFallbackState(snapshot: BootstrapSnapshot): BootstrapState {
  return {
    snapshot,
    branches: [],
    branchScope: [],
    setupRequired: false,
    source: "fallback",
  };
}

export async function fetchBootstrap(): Promise<BootstrapApiResponse> {
  // This GET itself issues the CSRF cookie; a preliminary bootstrap request
  // would duplicate the same read on every fresh browser session.
  return api<BootstrapApiResponse>("/api/v1/bootstrap");
}
