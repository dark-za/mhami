/** useBootstrap — hydrate :class:`BootstrapState` from ``/api/v1/bootstrap``.

Returns the live state plus ``loading`` and ``error`` flags. The hook
internally tracks an ``active`` flag so the state updates are discarded when
the component unmounts mid-flight.
*/

import { useEffect, useState } from "react";

import {
  createFallbackState,
  fetchBootstrap,
  type BootstrapState,
} from "../api/bootstrap";
import { bootstrapSnapshot } from "../design-system/tokens";
import type { BootstrapApiResponse } from "../api/contract";

function mergeBootstrap(state: BootstrapState, response: BootstrapApiResponse): BootstrapState {
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
    source: "live",
  };
}

function isBootstrapResponse(value: unknown): value is BootstrapApiResponse {
  return Boolean(value && typeof value === "object" && "current_user" in value);
}

export function useBootstrap() {
  const [state, setState] = useState<BootstrapState>(() => createFallbackState(bootstrapSnapshot));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = () => fetchBootstrap()
      .then((response) => {
        if (!active) {
          return;
        }
        setState((current) => mergeBootstrap(current, response));
        setError(null);
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setError(error instanceof Error ? error.message : "Bootstrap request failed.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    void load();

    const hydrateFromEvent = (event: Event) => {
      const detail = event instanceof CustomEvent ? event.detail : null;
      if (isBootstrapResponse(detail)) {
        setState((current) => mergeBootstrap(current, detail));
        setError(null);
        setLoading(false);
      } else {
        setLoading(true);
        void load();
      }
    };
    window.addEventListener("mhami.bootstrap.refreshed", hydrateFromEvent);

    return () => {
      active = false;
      window.removeEventListener("mhami.bootstrap.refreshed", hydrateFromEvent);
    };
  }, []);

  return { state, loading, error, setState };
}
