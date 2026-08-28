/** AppShell — top header + side rail + outlet for child routes.

Reads locale/calendar/role from :class:`useBootstrap` (state) and exposes
them via props to the children rendered through ``<Outlet />``. Auth-aware
navigation is also handled here.
*/

import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { Link, Outlet, useLocation } from "react-router";
import { useTranslation } from "react-i18next";

import { ensureCsrfToken, getCsrfToken } from "../api/client";
import { fetchBootstrap } from "../api/bootstrap";
import type { LoginRequest } from "../api/contract";
import {
  formatLocalizedDate,
  getVisibleNavItems,
  notificationSeed,
  readableTextColor,
  roleLabels,
  tintedSurface,
  type CalendarPreference,
  type Locale,
  type Role,
} from "../design-system/tokens";
import type { BootstrapState } from "../api/bootstrap";
import type { LiveNotification } from "../domain";
import { getWorkspaceRoute, routeTitle } from "../domain";
import { Badge, Panel } from "./ui";
import { CapabilityCard } from "./CapabilityCard";
import { useActiveRole } from "../hooks/useActiveRole";
import { LocaleSwitcher } from "../components/LocaleSwitcher";
import { useDirection } from "../hooks/useDirection";
import i18n from "../i18n";

const ROLE_STORAGE_KEY = "mhami.activeRole";

export interface AppShellProps {
  bootstrap: BootstrapState;
  setBootstrap: (updater: (current: BootstrapState) => BootstrapState) => void;
  loading: boolean;
  loadError: string | null;
  locale: Locale;
  setLocale: (next: Locale) => void;
  calendar: CalendarPreference;
  setCalendar: (next: CalendarPreference) => void;
  notifications: LiveNotification[] | null;
  notificationsError: boolean;
  children?: ReactNode;
}

export function AppShell(props: AppShellProps) {
  const {
    bootstrap,
    setBootstrap,
    loading,
    loadError,
    locale,
    setLocale,
    calendar,
    setCalendar,
    notifications,
    notificationsError,
  } = props;

  const role = useActiveRole();
  const setRole = (next: Role) => {
    if (typeof window === "undefined") {
      return;
    }
    try {
      window.localStorage.setItem(ROLE_STORAGE_KEY, next);
      window.dispatchEvent(
        new StorageEvent("storage", { key: ROLE_STORAGE_KEY, newValue: next }),
      );
    } catch (_error) {
      /* localStorage may be disabled; silently ignore */
    }
  };

  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [loginForm, setLoginForm] = useState({
    companyCode: bootstrap.snapshot.company.code,
    loginId: bootstrap.snapshot.currentUser.loginId,
    password: "",
    mfaCode: "",
  });
  const location = useLocation();
  const { i18n } = useTranslation();
  useDirection();

  useEffect(() => {
    document.documentElement.lang = locale === "ar" ? "ar" : "en";
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
    // Keep i18n aligned with the prop-driven locale in case callers
    // toggle the language through the chip controls.
    if (typeof i18n.changeLanguage === "function" && (i18n.resolvedLanguage ?? i18n.language) !== locale) {
      void i18n.changeLanguage(locale);
    }
  }, [locale, i18n]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    setAuthMessage(null);

    try {
      // C-04: use the shared client so the X-CSRFToken header is added
      // automatically and a missing cookie is surfaced as a 403 instead
      // of a silent 4xx.
      const body: LoginRequest = {
        company_code: loginForm.companyCode,
        login_id: loginForm.loginId,
        password: loginForm.password,
        mfa_code: loginForm.mfaCode || undefined,
      };
      await ensureCsrfToken();
      const csrfToken = getCsrfToken();
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail ?? `Login failed with ${response.status}`);
      }

      const bootstrapResponse = await fetchBootstrap();
      setBootstrap((current) => ({
        ...current,
        snapshot: {
          ...current.snapshot,
          currentUser: {
            ...current.snapshot.currentUser,
            id: bootstrapResponse.current_user.id ?? current.snapshot.currentUser.id,
            loginId: bootstrapResponse.current_user.login_id ?? current.snapshot.currentUser.loginId,
            displayName:
              bootstrapResponse.current_user.display_name ?? current.snapshot.currentUser.displayName,
            authenticated: bootstrapResponse.current_user.is_authenticated,
          },
          company: bootstrapResponse.company
            ? {
                ...current.snapshot.company,
                name: bootstrapResponse.company.name ?? current.snapshot.company.name,
                code: bootstrapResponse.company.code ?? current.snapshot.company.code,
                status: bootstrapResponse.company.status ?? current.snapshot.company.status,
              }
            : current.snapshot.company,
          permissions: bootstrapResponse.permissions,
          enabledModules: bootstrapResponse.enabled_modules as typeof current.snapshot.enabledModules,
        },
        branches: bootstrapResponse.branches,
        source: "live",
      }));
      setAuthMessage("Session is live and bootstrap data has been refreshed.");
    } catch (error: unknown) {
      setAuthError(error instanceof Error ? error.message : "Login failed.");
    } finally {
      setAuthLoading(false);
    }
  }

  const visibleNav = getVisibleNavItems(role, bootstrap.snapshot.enabledModules);
  const company = bootstrap.snapshot.company;
  const brandingSurface = tintedSurface(company.branding.primary, 0.12);
  const textColor = readableTextColor(company.branding.primary);
  const today = formatLocalizedDate(new Date(), locale, calendar);
  const languageLabel = locale === "ar" ? "العربية" : "English";
  const calendarLabel = calendar === "gregorian" ? "Gregorian" : "Hijri";
  const activeRoute = getWorkspaceRoute(location.pathname);
  const routeSummary = routeTitle(locale, activeRoute);

  return (
    <main className="app-shell">
      {loadError ? (
        <aside className="notice notice-warning">
          <strong>Bootstrap fallback active.</strong>
          <p>{loadError}</p>
        </aside>
      ) : null}

      <aside className={`notice ${loading ? "notice-neutral" : "notice-success"}`}>
        <strong>
          {loading
            ? "Loading live bootstrap data"
            : bootstrap.source === "live"
            ? "Live bootstrap connected"
            : "Demo snapshot active"}
        </strong>
        <p>
          {loading
            ? "The shell is hydrating from the backend contract."
            : bootstrap.source === "live"
            ? "Frontend data now reflects the current authenticated session."
            : "Using the local fallback snapshot."}
        </p>
      </aside>

      <header className="shell-header" style={{ background: brandingSurface, color: textColor }}>
        <div>
          <p className="eyebrow">Modular Operations Platform</p>
          <h1>{company.name}</h1>
          <p className="shell-summary">
            {company.code} · {today}
          </p>
        </div>
        <div className="header-actions">
          <Badge tone="info">{roleLabels[role][locale]}</Badge>
          <Badge tone="neutral">{languageLabel}</Badge>
          <Badge tone="neutral">{calendarLabel}</Badge>
          <Badge tone="neutral">{routeSummary}</Badge>
          <LocaleSwitcher />
        </div>
      </header>

      <section className="shell-grid">
        <Panel eyebrow="Access Surface" title="Login and shell entry">
          <form className="form-stack" onSubmit={handleLogin}>
            <div className="form-grid">
              <label>
                <span>Company code</span>
                <input
                  value={loginForm.companyCode}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, companyCode: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>Login ID</span>
                <input
                  value={loginForm.loginId}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, loginId: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>Password</span>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, password: event.target.value }))
                  }
                />
              </label>
              <label>
                <span>MFA code</span>
                <input
                  inputMode="numeric"
                  placeholder="123456"
                  value={loginForm.mfaCode}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, mfaCode: event.target.value }))
                  }
                />
              </label>
            </div>
            <div className="inline-actions">
              <button className="primary-button" type="submit" disabled={authLoading}>
                {authLoading ? "Signing in..." : "Sign in"}
              </button>
              <button
                className="ghost-button"
                type="button"
                onClick={() =>
                  setLoginForm({
                    companyCode: company.code,
                    loginId: bootstrap.snapshot.currentUser.loginId,
                    password: "",
                    mfaCode: "",
                  })
                }
              >
                Reset
              </button>
            </div>
          </form>
          {authError ? <p className="status status-danger">{authError}</p> : null}
          {authMessage ? <p className="status status-success">{authMessage}</p> : null}
          <p className="muted">
            Login stays backend-authoritative. The shell only mirrors the approved contract.
          </p>
        </Panel>

        <Panel eyebrow="Controls" title="Locale and role preview">
          <div className="chip-row">
            {(["ar", "en"] as const).map((value) => (
              <button
                key={value}
                className={`chip ${locale === value ? "chip-active" : ""}`}
                onClick={() => setLocale(value)}
                type="button"
              >
                {value === "ar" ? "Arabic RTL" : "English LTR"}
              </button>
            ))}
            {(["gregorian", "hijri"] as const).map((value) => (
              <button
                key={value}
                className={`chip ${calendar === value ? "chip-active" : ""}`}
                onClick={() => setCalendar(value)}
                type="button"
              >
                {calendar === "gregorian" ? "Gregorian" : "Hijri"}
              </button>
            ))}
          </div>
          <div className="chip-row">
            {Object.keys(roleLabels).map((value) => {
              const nextRole = value as Role;
              return (
                <button
                  key={nextRole}
                  className={`chip ${role === nextRole ? "chip-active" : ""}`}
                  onClick={() => setRole(nextRole)}
                  type="button"
                >
                  {roleLabels[nextRole].en}
                </button>
              );
            })}
          </div>
        </Panel>

        <Panel eyebrow="Design System" title="Branding and tokens">
          <div className="token-grid">
            <div
              className="token-swatch"
              style={{ background: company.branding.primary, color: readableTextColor(company.branding.primary) }}
            >
              <span>Primary</span>
              <strong>{company.branding.primary}</strong>
            </div>
            <div
              className="token-swatch"
              style={{
                background: company.branding.secondary,
                color: readableTextColor(company.branding.secondary),
              }}
            >
              <span>Secondary</span>
              <strong>{company.branding.secondary}</strong>
            </div>
            <div
              className="token-swatch"
              style={{ background: company.branding.accent, color: readableTextColor(company.branding.accent) }}
            >
              <span>Accent</span>
              <strong>{company.branding.accent}</strong>
            </div>
          </div>
        </Panel>

        <Panel eyebrow="Navigation" title="Role-aware modules">
          <nav className="nav-list" aria-label="Role aware navigation">
            <Link to="/">{locale === "ar" ? "الملخص" : "Summary"}</Link>
            {visibleNav.map((item) => (
              <Link key={item.module} to={`/${item.module}`}>
                <span>{locale === "ar" ? item.labelAr : item.labelEn}</span>
                <small>{item.module}</small>
              </Link>
            ))}
          </nav>
          <p className="muted">
            Only approved modules appear for the active role and live bootstrap snapshot when available.
          </p>
        </Panel>

        <Panel eyebrow="Notifications" title="In-app notification center">
          <div className="notification-list">
            {notificationsError || notifications === null
              ? notificationSeed.map((item) => (
                  <div key={item.id} className="notification-item">
                    <strong>{locale === "ar" ? item.titleAr : item.titleEn}</strong>
                    <p>{locale === "ar" ? item.bodyAr : item.bodyEn}</p>
                  </div>
                ))
              : notifications.length > 0
              ? notifications.map((item) => (
                  <div key={item.id} className="notification-item">
                    <strong>{item.title}</strong>
                    <p>{item.body || item.severity}</p>
                    <small>{item.read_at ? `Read ${item.read_at}` : "Unread"}</small>
                  </div>
                ))
              : (
                <p className="muted">No notifications yet.</p>
              )}
          </div>
        </Panel>

        <Panel eyebrow="Chrome" title="Capability preflight">
          <CapabilityCard />
        </Panel>

        {props.children}
      </section>

      <Outlet />
    </main>
  );
}
