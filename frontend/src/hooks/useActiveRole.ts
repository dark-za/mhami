/**
 * useActiveRole — single source of truth for the role the shell renders.
 * The live bootstrap response is the only source of role state. Client-side
 * preview overrides are deliberately not supported in the product shell.
 */
import type { BootstrapState } from "../api/bootstrap";
import type { Role } from "../design-system/tokens";

export function useActiveRole(bootstrap?: BootstrapState): Role | null {
  return (
    bootstrap?.source === "live" && bootstrap.snapshot.currentUser.authenticated === true
      ? bootstrap.snapshot.currentUser.role
      : null
  );
}
