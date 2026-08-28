/**
 * Application shell + bootstrap composition.
 *
 * The router itself is mounted in `main.tsx`. This file composes the
 * `AppShell` chrome (header, login form, navigation rail, notifications)
 * with the `AppRoutes` route table. The `RoleGuard` is delegated to
 * `routes/index.tsx` so the route table is the single source of truth for
 * the workspace surface area.
 */

import { useMemo, useState } from "react";

import { AppShell } from "./shell/AppShell";
import { AppRoutes } from "./routes";
import { useBootstrap } from "./hooks/useBootstrap";
import { useNotifications } from "./hooks/useNotifications";
import {
  bootstrapSnapshot,
  type CalendarPreference,
  type Locale,
} from "./design-system/tokens";
import type { BootstrapState } from "./api/bootstrap";

function AppShellHost() {
  const { state, loading, error, setState } = useBootstrap();
  const { items: notifications, error: notificationsError } = useNotifications();
  const [locale, setLocale] = useState<Locale>(bootstrapSnapshot.company.locale);
  const [calendar, setCalendar] = useState<CalendarPreference>("gregorian");
  const [activeTaskId, setActiveTaskId] = useState<string>("");

  const setBootstrap = useMemo(
    () => (updater: (current: BootstrapState) => BootstrapState) => {
      setState(updater);
    },
    [setState],
  );

  return (
    <AppShell
      bootstrap={state}
      setBootstrap={setBootstrap}
      loading={loading}
      loadError={error}
      locale={locale}
      setLocale={setLocale}
      calendar={calendar}
      setCalendar={setCalendar}
      notifications={notifications}
      notificationsError={notificationsError}
    >
      <AppRoutes
        onTaskSelected={setActiveTaskId}
        activeTaskId={activeTaskId}
        activeLocale={locale}
        bootstrap={state}
      />
    </AppShell>
  );
}

export function App() {
  return <AppShellHost />;
}
