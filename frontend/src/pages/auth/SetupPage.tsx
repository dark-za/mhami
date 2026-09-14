/** One-time first-owner setup for a new self-hosted installation. */
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";

import { api } from "../../api/client";
import { fetchBootstrap } from "../../api/bootstrap";
import { broadcastSessionChange } from "../../api/session";
import { defaultRouteForRole } from "../../domain/routing";
import type { Role } from "../../design-system/tokens";
import { Panel } from "../../shell/ui";
import { LocaleSwitcher } from "../../components/LocaleSwitcher";

type SetupForm = {
  organization_name: string;
  owner_display_name: string;
  owner_login_id: string;
  password: string;
  setup_token: string;
};

export function SetupPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState<SetupForm>({
    organization_name: "",
    owner_display_name: "",
    owner_login_id: "",
    password: "",
    setup_token: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);

  const update = <K extends keyof SetupForm>(field: K, value: SetupForm[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api("/api/v1/setup/initialize", { method: "POST", body: form });
      broadcastSessionChange();
      const bootstrap = await fetchBootstrap();
      window.dispatchEvent(new CustomEvent("mhami.bootstrap.refreshed", { detail: bootstrap }));
      navigate(defaultRouteForRole(bootstrap.current_user.role as Role | null | undefined), { replace: true });
    } catch {
      // The server intentionally gives the same response for every rejected
      // initial-setup attempt; keep that security boundary in the UI too.
      setError(t("auth.setup_failed"));
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
      <Panel eyebrow={t("auth.setup_eyebrow")} title={t("auth.setup_title")}>
        <p className="muted">{t("auth.setup_subtitle")}</p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            <span>{t("auth.organization_name")}</span>
            <input name="organization_name" dir="auto" autoComplete="organization" required value={form.organization_name} onChange={(event) => update("organization_name", event.target.value)} />
          </label>
          <label>
            <span>{t("auth.owner_display_name")}</span>
            <input name="owner_display_name" dir="auto" autoComplete="name" value={form.owner_display_name} onChange={(event) => update("owner_display_name", event.target.value)} />
          </label>
          <label>
            <span>{t("auth.login_id")}</span>
            <input name="owner_login_id" dir="ltr" autoComplete="username" required value={form.owner_login_id} onChange={(event) => update("owner_login_id", event.target.value)} />
          </label>
          <div className="form-field">
            <label htmlFor="setup-password">{t("auth.password")}</label>
            <span className="password-input">
              <input id="setup-password" name="password" type={passwordVisible ? "text" : "password"} dir="ltr" autoComplete="new-password" required minLength={12} value={form.password} onChange={(event) => update("password", event.target.value)} />
              <button className="field-icon-button" type="button" aria-label={passwordVisible ? t("auth.hide_password") : t("auth.show_password")} title={passwordVisible ? t("auth.hide_password") : t("auth.show_password")} onClick={() => setPasswordVisible((visible) => !visible)}>
                {passwordVisible ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
              </button>
            </span>
          </div>
          <label>
            <span>{t("auth.setup_token")}</span>
            <input name="setup_token" type="password" dir="ltr" autoComplete="off" required minLength={16} value={form.setup_token} onChange={(event) => update("setup_token", event.target.value)} />
          </label>
          {error ? <p className="error" role="alert">{error}</p> : null}
          <button className="primary-button login-submit" type="submit" disabled={loading}>
            {loading ? t("common.loading") : t("auth.setup_submit")}
          </button>
        </form>
        <p className="auth-link"><Link to="/login">{t("auth.login_link")}</Link></p>
        <p className="login-security-note"><ShieldCheck size={16} aria-hidden="true" /> {t("auth.setup_security")}</p>
      </Panel>
    </div>
  );
}

export default SetupPage;
