/** Load notifications only for the current authenticated session. */

import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { LiveNotification } from "../domain";

export function useNotifications(sessionKey: string | null) {
  const [result, setResult] = useState<{
    sessionKey: string | null;
    items: LiveNotification[] | null;
    error: boolean;
  }>({ sessionKey: null, items: null, error: false });

  useEffect(() => {
    setResult({ sessionKey, items: null, error: false });
    if (sessionKey === null) return;
    let active = true;
    const controller = new AbortController();

    void api<{ notifications?: LiveNotification[] }>("/api/v1/notifications/", { signal: controller.signal })
      .then((payload) => {
        if (active) {
          setResult({ sessionKey, items: payload.notifications ?? [], error: false });
        }
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setResult({ sessionKey, items: null, error: true });
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [sessionKey]);

  return sessionKey !== null && result.sessionKey === sessionKey
    ? { items: result.items, error: result.error }
    : { items: null, error: false };
}
