/** useNotifications — poll ``/api/v1/notifications/`` once on mount.

Falls back to ``null`` (sentinel for "unknown") if the backend errors out so
the shell can render a seeded demo set instead of an empty list.
*/

import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { LiveNotification } from "../domain";

export function useNotifications() {
  const [items, setItems] = useState<LiveNotification[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;

    void api<{ notifications?: LiveNotification[] }>("/api/v1/notifications/")
      .then((payload) => {
        if (active) {
          setItems(payload.notifications ?? []);
        }
      })
      .catch((reason: unknown) => {
        if (!active) {
          return;
        }
        if (reason instanceof ApiError) {
          setError(true);
        } else {
          setError(true);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return { items, error };
}
