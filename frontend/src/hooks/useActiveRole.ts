/**
 * useActiveRole — single source of truth for the role the shell is
 * currently rendering as. Falls back to the bootstrap snapshot role when no
 * override is persisted in `localStorage` (e.g. during preview builds).
 */
import { useEffect, useState } from "react";

import { bootstrapSnapshot, type Role } from "../design-system/tokens";

const STORAGE_KEY = "mhami.activeRole";

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

export function useActiveRole(): Role {
  const [role, setRole] = useState<Role>(() => readPersistedRole() ?? bootstrapSnapshot.currentUser.role);

  useEffect(() => {
    const handler = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) {
        setRole(readPersistedRole() ?? bootstrapSnapshot.currentUser.role);
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  return role;
}
