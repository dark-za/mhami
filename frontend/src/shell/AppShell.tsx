/** Authenticated workspace chrome. Login is rendered only by LoginPage. */

import { useState } from "react";
import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router";
import { useTranslation } from "react-i18next";
import {
  Bell,
  Bot,
  CalendarDays,
  CheckSquare,
  ChevronLeft,
  ClipboardCheck,
  FileArchive,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";

import type { BootstrapState } from "../api/bootstrap";
import {
  formatLocalizedDate,
  getVisibleNavItems,
  readableTextColor,
  roleLabels,
  tintedSurface,
  type CalendarPreference,
  type Locale,
} from "../design-system/tokens";
import type { LiveNotification } from "../domain";
import { getWorkspaceRoute, routeTitle } from "../domain";
import { useActiveRole } from "../hooks/useActiveRole";
import { LocaleSwitcher } from "../components/LocaleSwitcher";
import { Badge } from "./ui";
const IS_DEVELOPMENT = import.meta.env.DEV;

const navIcons = {
  dashboard: LayoutDashboard,
  operations: FileArchive,
  tasks: CheckSquare,
  evidence: ClipboardCheck,
  people: Users,
  reviews: ShieldCheck,
  admin: Settings,
  agent_access: Bot,
};

export interface AppShellProps {
  bootstrap: BootstrapState;
  loadError: string | null;
  locale: Locale;
  setLocale: (next: Locale) => void;
  calendar: CalendarPreference;
  setCalendar: (next: CalendarPreference) => void;
  notifications: LiveNotification[] | null;
  notificationsError: boolean;
  onLogout: () => Promise<void>;
  children?: ReactNode;
}

export function AppShell(props: AppShellProps) {
  const { t } = useTranslation();
  const {
    bootstrap,
    loadError,
    locale,
    setLocale,
    calendar,
    setCalendar,
    notifications,
    notificationsError,
    onLogout,
    children,
  } = props;
  const role = useActiveRole(bootstrap);
  const location = useLocation();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);

  const handleLogout = async () => {
    setLoggingOut(true);
    setLogoutError(null);
    try {
      await onLogout();
    } catch (_error: unknown) {
      setLogoutError(t("shell.sign_out_failed"));
    } finally {
      setLoggingOut(false);
    }
  };

  const visibleNav = getVisibleNavItems(role, bootstrap.snapshot.enabledModules);
  const company = bootstrap.snapshot.company;
  const brandingSurface = tintedSurface(company.branding.primary, 0.12);
  const textColor = readableTextColor(company.branding.primary);
  const today = formatLocalizedDate(new Date(), locale, calendar);
  const calendarLabel = calendar === "gregorian" ? t("shell.gregorian") : t("shell.hijri");
  const logoutLabel = t("common.logout");
  const notificationsLabel = t("shell.notifications");
  const activeRoute = getWorkspaceRoute(location.pathname);
  const routeSummary = routeTitle(locale, activeRoute);
  const unreadCount = notifications?.filter((item) => !item.read_at).length ?? 0;

  return (
    <main className="app-shell">
      <header className="workspace-header" style={{ background: brandingSurface, color: textColor }}>
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">M</span>
          <div>
            <p className="eyebrow">Mhami</p>
            <p className="company-name">{company.name}</p>
            <p className="shell-summary"><bdi>{company.code}</bdi> · <bdi>{today}</bdi></p>
          </div>
        </div>
        <div className="header-actions">
          <Badge tone="info">{role ? t(`people.role.${role}`, { defaultValue: roleLabels[role][locale] }) : ""}</Badge>
          <span className="route-title">{routeSummary}</span>
          <LocaleSwitcher onLocaleChange={setLocale} />
          <button className="icon-button" type="button" aria-label={t("shell.toggle_calendar")} title={calendarLabel} onClick={() => setCalendar(calendar === "gregorian" ? "hijri" : "gregorian")}>
            <CalendarDays size={18} aria-hidden="true" />
          </button>
          <button className="icon-button" type="button" aria-label={notificationsLabel} title={notificationsLabel}>
            <Bell size={18} aria-hidden="true" />
            {unreadCount > 0 ? <span className="notification-count">{unreadCount}</span> : null}
          </button>
          <button className="logout-button" type="button" onClick={() => void handleLogout()} disabled={loggingOut}>
            <LogOut size={17} aria-hidden="true" />
            <span>{loggingOut ? t("shell.signing_out") : logoutLabel}</span>
          </button>
        </div>
      </header>

      <div className="workspace-layout">
        <aside className="workspace-sidebar">
          <nav className="nav-list" aria-label={t("shell.role_aware_navigation")}>
            <NavLink className={({ isActive }) => `nav-link${isActive ? " nav-link-active" : ""}`} to="/">
              <CheckSquare size={18} aria-hidden="true" />
              <span>{t("nav.tasks")}</span>
            </NavLink>
            {visibleNav.filter((item) => item.module !== "tasks").map((item) => {
              const Icon = navIcons[item.module];
              return (
                <NavLink key={item.module} className={({ isActive }) => `nav-link${isActive ? " nav-link-active" : ""}`} to={item.href}>
                  <Icon size={18} aria-hidden="true" />
                  <span>{t(`nav.${item.module}`, { defaultValue: locale === "ar" ? item.labelAr : item.labelEn })}</span>
                  <ChevronLeft className="nav-chevron" size={16} aria-hidden="true" />
                </NavLink>
              );
            })}
          </nav>

          <section className="sidebar-settings" aria-label={t("shell.display_preferences")}>
            <p className="sidebar-label">{t("shell.display")}</p>
            <div className="chip-row">
              {(["gregorian", "hijri"] as const).map((value) => (
                <button key={value} className={`chip ${calendar === value ? "chip-active" : ""}`} onClick={() => setCalendar(value)} type="button">
                  {value === "gregorian" ? t("shell.gregorian") : t("shell.hijri")}
                </button>
              ))}
            </div>
          </section>

          <section className="sidebar-notifications" aria-label={notificationsLabel}>
            <div className="sidebar-section-title">
              <Bell size={16} aria-hidden="true" />
              <span>{notificationsLabel}</span>
            </div>
            {notificationsError || notifications === null
              ? <p className="sidebar-note">{t("shell.updates_available")}</p>
              : notifications.length > 0
                ? <p className="sidebar-note">{unreadCount > 0 ? t("shell.unread_updates", { count: unreadCount }) : t("shell.no_unread_updates")}</p>
                : <p className="sidebar-note">{t("shell.no_new_notifications")}</p>}
          </section>
        </aside>

        <section className="workspace-main">
          {loadError ? (
            <aside className="notice notice-warning" role="status">
              <strong>{t("shell.session_refresh_title")}</strong>
              <p>{t("shell.session_refresh_body")}</p>
              {IS_DEVELOPMENT ? <small>{loadError}</small> : null}
            </aside>
          ) : null}
          {logoutError ? <p className="status status-danger" role="alert">{logoutError}</p> : null}
          <section className="shell-grid">{children}</section>
        </section>
      </div>
    </main>
  );
}
