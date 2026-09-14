/** AgentAccessPage — owner console for MCP grants, scopes, and action logs. */

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Check, Copy } from "lucide-react";
import { useTranslation } from "react-i18next";

import { api } from "../../api/client";
import { EmptyState, Panel, SkeletonBlock } from "../../shell/ui";
import type { AgentActionLog, AgentGrant, AgentScope, CompanyMemberOption } from "../../domain";

const DEFAULT_SCOPES = ["read:tasks"];
const DEFAULT_DIGEST = "sha256:" + "0".repeat(64);

type MembersPayload = {
  memberships?: Array<{
    user?: string;
    user_id?: string;
    display_name?: string;
    login_id?: string;
    role?: string;
    active?: boolean;
  }>;
};

type CreatedGrant = AgentGrant & { secret?: string };

function tomorrowLocalInputValue(): string {
  const next = new Date();
  next.setDate(next.getDate() + 1);
  next.setMinutes(next.getMinutes() - next.getTimezoneOffset());
  return next.toISOString().slice(0, 16);
}

function toApiDateTime(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toISOString();
}

function formatDate(value: string | null, locale: string): string {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString(locale);
}

function scopeTranslationKey(scope: string): string {
  return scope.replaceAll(":", "_");
}

export function AgentAccessPage() {
  const { i18n, t } = useTranslation();
  const [grants, setGrants] = useState<AgentGrant[]>([]);
  const [scopes, setScopes] = useState<AgentScope[]>([]);
  const [logs, setLogs] = useState<AgentActionLog[]>([]);
  const [members, setMembers] = useState<CompanyMemberOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [issuedSecret, setIssuedSecret] = useState<string | null>(null);
  const [secretCopied, setSecretCopied] = useState(false);
  const [draft, setDraft] = useState({
    userId: "",
    clientName: t("agent_access.default_client_name"),
    clientFingerprint: DEFAULT_DIGEST,
    scopes: DEFAULT_SCOPES,
    expiresAt: tomorrowLocalInputValue(),
  });

  async function refresh() {
    const [grantPayload, scopePayload, logPayload, memberPayload] = await Promise.all([
      api<{ grants?: AgentGrant[] }>("/api/v1/agent/grants"),
      api<{ scopes?: AgentScope[] }>("/api/v1/agent/scopes"),
      api<{ logs?: AgentActionLog[] }>("/api/v1/agent/logs"),
      api<MembersPayload>("/api/v1/auth/company/members"),
    ]);
    const activeMembers =
      memberPayload.memberships
        ?.filter((membership) => membership.active !== false)
        .map((membership) => {
          const id = membership.user_id ?? membership.user ?? "";
          return {
            id,
            label: membership.display_name ?? membership.login_id ?? t("agent_access.team_member"),
            detail: membership.role
              ? t(`agent_access.role.${membership.role}`, { defaultValue: membership.role })
              : membership.login_id ?? t("agent_access.active_member"),
          };
        })
        .filter((member) => member.id) ?? [];

    setGrants(grantPayload.grants ?? []);
    setScopes(scopePayload.scopes ?? []);
    setLogs(logPayload.logs ?? []);
    setMembers(activeMembers);
    setDraft((current) => ({
      ...current,
      userId: current.userId || activeMembers[0]?.id || "",
    }));
  }

  useEffect(() => {
    let active = true;
    void refresh()
      .catch((_caught: unknown) => {
        if (active) {
          setError(t("agent_access.load_failed"));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const activeCount = useMemo(() => grants.filter((grant) => grant.active).length, [grants]);
  const revokedCount = useMemo(
    () => grants.filter((grant) => grant.status === "revoked").length,
    [grants],
  );

  function toggleScope(value: string) {
    setDraft((current) => {
      const nextScopes = current.scopes.includes(value)
        ? current.scopes.filter((scope) => scope !== value)
        : [...current.scopes, value];
      return { ...current, scopes: nextScopes.length > 0 ? nextScopes : current.scopes };
    });
  }

  async function refreshAfterMutation(successMessage: string) {
    setMessage(successMessage);
    try {
      await refresh();
    } catch {
      setMessage(`${successMessage} ${t("agent_access.refresh_notice")}`);
    }
  }

  async function createGrant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("create");
    setError(null);
    setMessage(null);
    setIssuedSecret(null);
    setSecretCopied(false);
    try {
      const created = await api<CreatedGrant>("/api/v1/agent/grants", {
        method: "POST",
        body: {
          user_id: draft.userId,
          client_name: draft.clientName,
          client_fingerprint: draft.clientFingerprint,
          scopes: draft.scopes,
          expires_at: toApiDateTime(draft.expiresAt),
        },
      });
      setIssuedSecret(created.secret ?? null);
      await refreshAfterMutation(t("agent_access.grant_created"));
    } catch (_caught: unknown) {
      setError(t("agent_access.create_failed"));
    } finally {
      setSaving(null);
    }
  }

  async function copyIssuedSecret() {
    if (!issuedSecret) return;
    try {
      await navigator.clipboard.writeText(issuedSecret);
      setSecretCopied(true);
    } catch {
      setError(t("agent_access.copy_failed"));
    }
  }

  async function revokeGrant(grantId: string) {
    setSaving(grantId);
    setError(null);
    setMessage(null);
    try {
      await api<AgentGrant>(`/api/v1/agent/grants/${grantId}/revoke`, {
        method: "POST",
        body: { reason: "owner_console_revoke" },
      });
      await refreshAfterMutation(t("agent_access.grant_revoked"));
    } catch (_caught: unknown) {
      setError(t("agent_access.revoke_failed"));
    } finally {
      setSaving(null);
    }
  }

  return (
    <Panel eyebrow={t("agent_access.eyebrow")} title={t("agent_access.title")} variant="action">
      {error ? <p className="status status-danger">{error}</p> : null}
      {message ? <p className="status status-success">{message}</p> : null}
      {loading ? <SkeletonBlock rows={5} /> : null}

      {!loading ? (
        <>
          {issuedSecret ? (
            <section className="state-card state-warning" aria-live="polite">
              <strong>{t("agent_access.secret_title")}</strong>
              <p>{t("agent_access.secret_notice")}</p>
              <div className="inline-actions">
                <input className="bidi-ltr" dir="ltr" aria-label={t("agent_access.secret_title")} readOnly value={issuedSecret} />
                <button className="ghost-button" type="button" onClick={() => void copyIssuedSecret()}>
                  {secretCopied ? <Check aria-hidden="true" size={16} /> : <Copy aria-hidden="true" size={16} />}
                  <span>{secretCopied ? t("agent_access.copied") : t("agent_access.copy")}</span>
                </button>
              </div>
            </section>
          ) : null}
          <div className="state-grid">
            <div className="state-card state-neutral">
              <strong>{activeCount}</strong>
              <p>{t("agent_access.active_grants")}</p>
            </div>
            <div className="state-card state-warning">
              <strong>{revokedCount}</strong>
              <p>{t("agent_access.revoked_grants")}</p>
            </div>
          </div>

          <form className="form-stack" onSubmit={createGrant}>
            <div className="form-grid">
              <label>
                <span>{t("agent_access.grant_user")}</span>
                <select
                  value={draft.userId}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, userId: event.target.value }))
                  }
                >
                  <option value="">{t("agent_access.select_member")}</option>
                  {members.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.label} · {member.detail}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>{t("agent_access.client_name")}</span>
                <input
                  value={draft.clientName}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, clientName: event.target.value }))
                  }
                />
              </label>
            </div>
            <label>
              <span>{t("agent_access.client_fingerprint")}</span>
              <input
                className="bidi-ltr"
                dir="ltr"
                value={draft.clientFingerprint}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, clientFingerprint: event.target.value }))
                }
              />
            </label>
            <div className="form-grid">
              <label>
                <span>{t("agent_access.expires_at_label")}</span>
                <input
                  type="datetime-local"
                  className="bidi-ltr"
                  dir="ltr"
                  value={draft.expiresAt}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, expiresAt: event.target.value }))
                  }
                />
              </label>
              <div className="scope-picker" aria-label={t("agent_access.scopes")}>
                {scopes.map((scope) => (
                  <label key={scope.value} className="scope-option">
                    <input
                      type="checkbox"
                      checked={draft.scopes.includes(scope.value)}
                      onChange={() => toggleScope(scope.value)}
                    />
                    <span title={scope.value}>
                      {t(`agent_access.scope.${scopeTranslationKey(scope.value)}`, { defaultValue: scope.value })}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <button className="primary-button" type="submit" disabled={saving === "create"}>
              {t("agent_access.create_grant")}
            </button>
          </form>

          <div className="notification-list">
            {grants.map((grant) => (
              <div key={grant.id} className="notification-item">
                <div className="split-row">
                  <strong>{grant.client_name}</strong>
                  <span className={`badge ${grant.active ? "badge-success" : "badge-neutral"}`}>
                    {t(`agent_access.status.${grant.active ? "active" : grant.status}`, {
                      defaultValue: grant.active ? "active" : grant.status,
                    })}
                  </span>
                </div>
                <p>
                  {grant.scopes
                    .map((scope) =>
                      t(`agent_access.scope.${scopeTranslationKey(scope)}`, { defaultValue: scope }),
                    )
                    .join(", ")}
                </p>
                <small>
                  <bdi>{grant.client_fingerprint.slice(0, 20)}...</bdi> · {t("agent_access.expires_at", {
                    date: formatDate(grant.expires_at, i18n.language),
                  })}
                </small>
                <div className="inline-actions">
                  <button
                    className="ghost-button"
                    type="button"
                    disabled={Boolean(saving) || !grant.active}
                    onClick={() => void revokeGrant(grant.id)}
                  >
                    {t("agent_access.revoke")}
                  </button>
                </div>
              </div>
            ))}
            {grants.length === 0 ? (
              <EmptyState
                title={t("agent_access.no_grants")}
                body={t("agent_access.no_grants_body")}
              />
            ) : null}
          </div>

          <div className="audit-list">
            <h3>{t("agent_access.recent_actions")}</h3>
            {logs.map((log) => (
              <div key={log.id} className="audit-row">
                <bdi>{log.tool_name}</bdi>
                <bdi>{log.required_scope}</bdi>
                <span>{t(`agent_access.action_status.${log.status}`, { defaultValue: log.status })}</span>
                <small>{formatDate(log.created_at, i18n.language)}</small>
              </div>
            ))}
            {logs.length === 0 ? (
              <EmptyState
                title={t("agent_access.no_activity")}
                body={t("agent_access.no_activity_body")}
              />
            ) : null}
          </div>
        </>
      ) : null}
    </Panel>
  );
}

export default AgentAccessPage;
