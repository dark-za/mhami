/** Login surface for the local, password-based account flow. */
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";

import { api } from "../../api/client";
import { fetchBootstrap } from "../../api/bootstrap";
import { broadcastSessionChange } from "../../api/session";
import { defaultRouteForRole } from "../../domain/routing";
import type { Role } from "../../design-system/tokens";
import { Panel } from "../../shell/ui";
import { LocaleSwitcher } from "../../components/LocaleSwitcher";

export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ login_id: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api("/api/v1/auth/login", { method: "POST", body: form });
      broadcastSessionChange();
      const bootstrap = await fetchBootstrap();
      window.dispatchEvent(new CustomEvent("mhami.bootstrap.refreshed", { detail: bootstrap }));
      navigate(defaultRouteForRole(bootstrap.current_user.role as Role | null | undefined), { replace: true });
    } catch {
      // Login failures deliberately remain generic: exposing authentication
      // details would help account enumeration and breaks the active locale.
      setError(t("auth.login_failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-locale-switcher">
        <LocaleSwitcher />
      </div>
      <div className="login-brand" aria-hidden="true">
        <span className="brand-mark">M</span>
        <span>Mhami</span>
      </div>
      <Panel eyebrow={t("common.login")} title={t("auth.login_title")}>
        <p className="muted">{t("auth.login_subtitle")}</p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            <span>{t("auth.login_id")}</span>
            <input
              name="login_id"
              dir="ltr"
              autoComplete="username"
              required
              value={form.login_id}
              onChange={(event) => setForm({ ...form, login_id: event.target.value })}
            />
          </label>
          <div className="form-field">
            <label htmlFor="password">{t("auth.password")}</label>
            <span className="password-input">
              <input
                id="password"
                name="password"
                type={passwordVisible ? "text" : "password"}
                dir="ltr"
                autoComplete="current-password"
                required
                value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
              />
              <button
                className="field-icon-button"
                type="button"
                aria-label={passwordVisible ? t("auth.hide_password") : t("auth.show_password")}
                title={passwordVisible ? t("auth.hide_password") : t("auth.show_password")}
                onClick={() => setPasswordVisible((visible) => !visible)}
              >
                {passwordVisible ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
              </button>
            </span>
          </div>
          {error ? <p className="error" role="alert">{error}</p> : null}
          <button className="primary-button login-submit" type="submit" disabled={loading}>
            {loading ? t("common.loading") : t("common.login")}
          </button>
        </form>
        <p className="login-security-note"><ShieldCheck size={16} aria-hidden="true" /> {t("auth.login_security")}</p>
      </Panel>
    </div>
  );
}

export default LoginPage;
