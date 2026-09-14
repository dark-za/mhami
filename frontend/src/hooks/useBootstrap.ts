/** Hydrate bootstrap while discarding replies superseded by session changes. */

import { useCallback, useEffect, useRef, useState, type SetStateAction } from "react";

import {
  createFallbackState,
  fetchBootstrap,
  type BootstrapState,
} from "../api/bootstrap";
import { bootstrapSnapshot } from "../design-system/tokens";
import type { BootstrapApiResponse } from "../api/contract";
import { SESSION_CHANGE_KEY, SESSION_RECHECK_EVENT } from "../api/session";

function mergeBootstrap(response: BootstrapApiResponse): BootstrapState {
  const state = createFallbackState(bootstrapSnapshot);
  return {
    snapshot: {
      ...state.snapshot,
      currentUser: {
        ...state.snapshot.currentUser,
        id: response.current_user.id ?? state.snapshot.currentUser.id,
        loginId: response.current_user.login_id ?? state.snapshot.currentUser.loginId,
        displayName: response.current_user.display_name ?? state.snapshot.currentUser.displayName,
        authenticated: response.current_user.is_authenticated,
        role: (response.current_user.role as BootstrapState["snapshot"]["currentUser"]["role"]) ?? null,
      },
      company: response.company
        ? {
            ...state.snapshot.company,
            id: response.company.id ?? state.snapshot.company.id,
            name: response.company.name ?? state.snapshot.company.name,
            code: response.company.code ?? state.snapshot.company.code,
            status: response.company.status ?? state.snapshot.company.status,
          }
        : state.snapshot.company,
      permissions: response.permissions,
      enabledModules: response.enabled_modules as typeof state.snapshot.enabledModules,
    },
    branches: response.branches,
    branchScope: response.branch_scope ?? [],
    setupRequired: response.installation.setup_required,
    source: "live",
  };
}

function isBootstrapResponse(value: unknown): value is BootstrapApiResponse {
  return Boolean(value && typeof value === "object" && "current_user" in value);
}

export function useBootstrap() {
  const [state, commitState] = useState<BootstrapState>(() => createFallbackState(bootstrapSnapshot));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const revision = useRef(0);

  const setState = useCallback((next: SetStateAction<BootstrapState>) => {
    // Logout invalidates requests issued under the previous session.
    revision.current += 1;
    commitState(next);
    setLoading(false);
    setError(null);
  }, []);

  useEffect(() => {
    let active = true;
    let recheckPending = false;

    const load = () => {
      const requestRevision = ++revision.current;
      const isCurrent = () => active && requestRevision === revision.current;
      return fetchBootstrap()
        .then((response) => {
          if (!isCurrent()) return;
          commitState(mergeBootstrap(response));
          setError(null);
        })
        .catch(() => {
          if (!isCurrent()) return;
          commitState(createFallbackState(bootstrapSnapshot));
          setError("bootstrap_failed");
        })
        .finally(() => {
          if (isCurrent()) setLoading(false);
        });
    };

    void load();

    const hydrateFromEvent = (event: Event) => {
      const detail = event instanceof CustomEvent ? event.detail : null;
      if (isBootstrapResponse(detail)) {
        revision.current += 1;
        commitState(mergeBootstrap(detail));
        setError(null);
        setLoading(false);
      } else {
        setLoading(true);
        void load();
      }
    };
    const recheckSession = (hideWorkspace: boolean) => {
      if (hideWorkspace) {
        commitState(createFallbackState(bootstrapSnapshot));
        setLoading(true);
      }
      if (recheckPending && !hideWorkspace) return;
      recheckPending = true;
      void load().finally(() => { recheckPending = false; });
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key === SESSION_CHANGE_KEY) recheckSession(true);
    };
    const onSessionRejected = () => recheckSession(true);
    const onFocus = () => {
      if (document.visibilityState === "visible") recheckSession(false);
    };
    window.addEventListener("mhami.bootstrap.refreshed", hydrateFromEvent);
    window.addEventListener("storage", onStorage);
    window.addEventListener(SESSION_RECHECK_EVENT, onSessionRejected);
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);

    return () => {
      active = false;
      window.removeEventListener("mhami.bootstrap.refreshed", hydrateFromEvent);
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(SESSION_RECHECK_EVENT, onSessionRejected);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, []);

  return { state, loading, error, setState };
}
