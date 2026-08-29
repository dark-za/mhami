/** AgentAccessPage — owner console for MCP grants, scopes, and action logs. */

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

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

function formatDate(value: string | null): string {
  if (!value) {
    return "not set";
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

export function AgentAccessPage() {
  const [grants, setGrants] = useState<AgentGrant[]>([]);
  const [scopes, setScopes] = useState<AgentScope[]>([]);
  const [logs, setLogs] = useState<AgentActionLog[]>([]);
  const [members, setMembers] = useState<CompanyMemberOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState({
    userId: "",
    clientName: "Owner MCP client",
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
            label: membership.display_name ?? membership.login_id ?? "Team member",
            detail: membership.role ?? membership.login_id ?? "Active member",
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
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "MCP access failed to load.");
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

  async function createGrant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("create");
    setError(null);
    setMessage(null);
    try {
      await api<AgentGrant>("/api/v1/agent/grants", {
        method: "POST",
        body: {
          user_id: draft.userId,
          client_name: draft.clientName,
          client_fingerprint: draft.clientFingerprint,
          scopes: draft.scopes,
          expires_at: toApiDateTime(draft.expiresAt),
        },
      });
      await refresh();
      setMessage("MCP access grant created.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Grant creation failed.");
    } finally {
      setSaving(null);
    }
  }

  async function revokeGrant(grantId: string) {
    setSaving(grantId);
    setError(null);
    setMessage(null);
    try {
      await api<AgentGrant>(`/api/v1/agent/grants/${grantId}/revoke`, {
        method: "POST",
        body: { reason: "Revoked from owner console" },
      });
      await refresh();
      setMessage("MCP access grant revoked.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Grant revoke failed.");
    } finally {
      setSaving(null);
    }
  }

  return (
    <Panel eyebrow="MCP access" title="Agent grants and audit trail" variant="action">
      {error ? <p className="status status-danger">{error}</p> : null}
      {message ? <p className="status status-success">{message}</p> : null}
      {loading ? <SkeletonBlock rows={5} /> : null}

      {!loading ? (
        <>
          <div className="state-grid">
            <div className="state-card state-neutral">
              <strong>{activeCount}</strong>
              <p>Active grants</p>
            </div>
            <div className="state-card state-warning">
              <strong>{revokedCount}</strong>
              <p>Revoked grants</p>
            </div>
          </div>

          <form className="form-stack" onSubmit={createGrant}>
            <div className="form-grid">
              <label>
                <span>Grant user</span>
                <select
                  value={draft.userId}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, userId: event.target.value }))
                  }
                >
                  <option value="">Select a company member</option>
                  {members.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.label} · {member.detail}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Client name</span>
                <input
                  value={draft.clientName}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, clientName: event.target.value }))
                  }
                />
              </label>
            </div>
            <label>
              <span>Client fingerprint</span>
              <input
                value={draft.clientFingerprint}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, clientFingerprint: event.target.value }))
                }
              />
            </label>
            <div className="form-grid">
              <label>
                <span>Expires at</span>
                <input
                  type="datetime-local"
                  value={draft.expiresAt}
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, expiresAt: event.target.value }))
                  }
                />
              </label>
              <div className="scope-picker" aria-label="MCP scopes">
                {scopes.map((scope) => (
                  <label key={scope.value} className="scope-option">
                    <input
                      type="checkbox"
                      checked={draft.scopes.includes(scope.value)}
                      onChange={() => toggleScope(scope.value)}
                    />
                    <span>{scope.value}</span>
                  </label>
                ))}
              </div>
            </div>
            <button className="primary-button" type="submit" disabled={saving === "create"}>
              Create grant
            </button>
          </form>

          <div className="notification-list">
            {grants.map((grant) => (
              <div key={grant.id} className="notification-item">
                <div className="split-row">
                  <strong>{grant.client_name}</strong>
                  <span className={`badge ${grant.active ? "badge-success" : "badge-neutral"}`}>
                    {grant.active ? "active" : grant.status}
                  </span>
                </div>
                <p>{grant.scopes.join(", ")}</p>
                <small>
                  {grant.client_fingerprint.slice(0, 20)}... · expires {formatDate(grant.expires_at)}
                </small>
                <div className="inline-actions">
                  <button
                    className="ghost-button"
                    type="button"
                    disabled={Boolean(saving) || !grant.active}
                    onClick={() => void revokeGrant(grant.id)}
                  >
                    Revoke
                  </button>
                </div>
              </div>
            ))}
            {grants.length === 0 ? (
              <EmptyState title="No MCP grants" body="Owner-created agent grants will appear here." />
            ) : null}
          </div>

          <div className="audit-list">
            <h3>Recent agent actions</h3>
            {logs.map((log) => (
              <div key={log.id} className="audit-row">
                <span>{log.tool_name}</span>
                <span>{log.required_scope}</span>
                <span>{log.status}</span>
                <small>{formatDate(log.created_at)}</small>
              </div>
            ))}
            {logs.length === 0 ? (
              <EmptyState title="No agent activity" body="MCP tool calls are listed after execution." />
            ) : null}
          </div>
        </>
      ) : null}
    </Panel>
  );
}

export default AgentAccessPage;
