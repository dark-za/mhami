/**
 * useActiveRole — single source of truth for the role the shell renders.
 * Production builds trust only the live bootstrap response. The localStorage
 * override is reserved for development previews.
 */
import { useEffect, useState } from "react";

import type { BootstrapState } from "../api/bootstrap";
import type { Role } from "../design-system/tokens";

const STORAGE_KEY = "mhami.activeRole";
const IS_DEVELOPMENT = import.meta.env.DEV;

function readPersistedRole(): Role | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    if (!value) {
      return null;
    }
    const candidates: Role[] = ["platform_admin", "owner", "monitor", "employee"];
    return candidates.includes(value as Role) ? (value as Role) : null;
  } catch (_error) {
    return null;
  }
}

export function useActiveRole(bootstrap?: BootstrapState): Role | null {
  const liveRole =
    bootstrap?.source === "live" && bootstrap.snapshot.currentUser.authenticated === true
      ? bootstrap.snapshot.currentUser.role
      : null;
  const [previewRole, setPreviewRole] = useState<Role | null>(() => (IS_DEVELOPMENT ? readPersistedRole() : null));

  useEffect(() => {
    if (!IS_DEVELOPMENT) {
      return undefined;
    }
    const handler = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) {
        setPreviewRole(readPersistedRole());
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  return liveRole ?? (IS_DEVELOPMENT ? previewRole : null);
}
