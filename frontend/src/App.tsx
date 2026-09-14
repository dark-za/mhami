/**
 * Application shell + bootstrap composition.
 *
 * The router itself is mounted in `main.tsx`. This file composes the
 * `AppShell` chrome (header, login form, navigation rail, notifications)
 * with the `AppRoutes` route table. The `RoleGuard` is delegated to
 * `routes/index.tsx` so the route table is the single source of truth for
 * the workspace surface area.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "./api/client";
import { broadcastSessionChange } from "./api/session";
import { createFallbackState } from "./api/bootstrap";
import { bootstrapSnapshot } from "./design-system/tokens";
import { AppShell } from "./shell/AppShell";
import { AppRoutes } from "./routes";
import { useBootstrap } from "./hooks/useBootstrap";
import { useNotifications } from "./hooks/useNotifications";
import { useDirection } from "./hooks/useDirection";
import {
  type CalendarPreference,
  type Locale,
} from "./design-system/tokens";
import i18n from "./i18n";

function initialLocale(): Locale {
  const language = i18n.resolvedLanguage ?? i18n.language;
  return language.startsWith("ar") ? "ar" : "en";
}

function AppShellHost() {
  const { i18n } = useTranslation();
  const { language } = useDirection();
  const { state, loading, error, setState } = useBootstrap();
  const authenticated =
    !loading && state.source === "live" && state.snapshot.currentUser.authenticated === true;
  const sessionKey = authenticated ? `${state.snapshot.company.id}:${state.snapshot.currentUser.id}` : null;
  const { items: notifications, error: notificationsError } = useNotifications(sessionKey);
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const [calendar, setCalendar] = useState<CalendarPreference>("gregorian");
  const [selection, setSelection] = useState<{ sessionKey: string | null; taskId: string }>({ sessionKey: null, taskId: "" });
  const activeTaskId = selection.sessionKey === sessionKey ? selection.taskId : "";
  const setActiveTaskId = (taskId: string) => setSelection({ sessionKey, taskId });

  useEffect(() => {
    const nextLocale: Locale = language.startsWith("ar") ? "ar" : "en";
    setLocale((current) => (current === nextLocale ? current : nextLocale));
  }, [language]);

  useEffect(() => {
    if ((i18n.resolvedLanguage ?? i18n.language) !== locale) {
      void i18n.changeLanguage(locale);
    }
  }, [i18n, locale]);

  const handleLogout = async () => {
    await api<void>("/api/v1/auth/logout", { method: "POST" });
    broadcastSessionChange();
    setState(createFallbackState(bootstrapSnapshot));
  };

  if (!authenticated) {
    return (
      <AppRoutes
        onTaskSelected={setActiveTaskId}
        activeTaskId={activeTaskId}
        activeLocale={locale}
        bootstrap={state}
        bootstrapLoading={loading}
      />
    );
  }

  return (
    <AppShell
      key={sessionKey}
      bootstrap={state}
      loadError={error}
      locale={locale}
      setLocale={setLocale}
      calendar={calendar}
      setCalendar={setCalendar}
      notifications={notifications}
      notificationsError={notificationsError}
      onLogout={handleLogout}
    >
      <AppRoutes
        onTaskSelected={setActiveTaskId}
        activeTaskId={activeTaskId}
        activeLocale={locale}
        bootstrap={state}
        bootstrapLoading={loading}
      />
    </AppShell>
  );
}

export function App() {
  return <AppShellHost />;
}
