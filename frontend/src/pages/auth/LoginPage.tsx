/**
 * LoginPage — minimal login surface used by the lazy `/login` route.
 *
 * The shell already ships a login form (`AppShell.handleLogin`) wired to
 * `/api/v1/auth/login`. This page is a standalone surface for the
 * unauthenticated flow and reuses the same backend contract.
 */
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";

import { api, ApiError } from "../../api/client";
import { fetchBootstrap } from "../../api/bootstrap";
import { Panel } from "../../shell/ui";

export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ company_code: "", login_id: "", password: "", mfa_code: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api("/api/v1/auth/login", {
        method: "POST",
        body: {
          company_code: form.company_code,
          login_id: form.login_id,
          password: form.password,
          mfa_code: form.mfa_code || undefined,
        },
      });
      // Touch bootstrap so the shell hydrates with the new session.
      await fetchBootstrap().catch(() => undefined);
      navigate("/", { replace: true });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : t("auth.login_failed");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <Panel eyebrow={t("common.login")} title={t("auth.login_title")}>
        <p className="muted">{t("auth.login_subtitle")}</p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            <span>{t("auth.company_code")}</span>
            <input
              name="company_code"
              autoComplete="organization"
              required
              value={form.company_code}
              onChange={(event) => setForm({ ...form, company_code: event.target.value })}
            />
          </label>
          <label>
            <span>{t("auth.login_id")}</span>
            <input
              name="login_id"
              autoComplete="username"
              required
              value={form.login_id}
              onChange={(event) => setForm({ ...form, login_id: event.target.value })}
            />
          </label>
          <label>
            <span>{t("auth.password")}</span>
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </label>
          <label>
            <span>{t("auth.mfa_code")}</span>
            <input
              name="mfa_code"
              inputMode="numeric"
              pattern="[0-9]*"
              value={form.mfa_code}
              onChange={(event) => setForm({ ...form, mfa_code: event.target.value })}
            />
          </label>
          {error ? (
            <p className="error" role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" disabled={loading}>
            {loading ? t("common.loading") : t("common.login")}
          </button>
        </form>
      </Panel>
    </div>
  );
}

export default LoginPage;
