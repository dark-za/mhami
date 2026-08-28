/** AIControlPage — provider configuration and connector enrollment. */

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../api/client";
import { Panel } from "../../shell/ui";
import type { AIProviderConfig, ConnectorEnrollment } from "../../domain";

interface ConnectorResponse {
  enrollment?: ConnectorEnrollment | null;
}

const PROVIDER_DRAFT_DEFAULT = {
  providerName: "fake",
  endpointUrl: "",
  modelName: "",
  credentialReference: "",
  monthlyTokenLimit: 10000,
  monthlyCostLimit: "0.00",
  enabled: true,
};

const CONNECTOR_DRAFT_DEFAULT = {
  connectorVersion: "1.0.0",
  sharedSecretFingerprint: "",
};

export function AIControlPage() {
  const [provider, setProvider] = useState<AIProviderConfig | null>(null);
  const [connector, setConnector] = useState<ConnectorEnrollment | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiMessage, setAiMessage] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState<string | null>(null);
  const [providerDraft, setProviderDraft] = useState(PROVIDER_DRAFT_DEFAULT);
  const [connectorDraft, setConnectorDraft] = useState(CONNECTOR_DRAFT_DEFAULT);

  async function refresh() {
    const [providerPayload, connectorPayload] = await Promise.all([
      api<AIProviderConfig>("/api/v1/ai/provider"),
      api<ConnectorResponse>("/api/v1/connectors/enrollment"),
    ]);
    setProvider(providerPayload);
    setProviderDraft({
      providerName: providerPayload.provider_name ?? PROVIDER_DRAFT_DEFAULT.providerName,
      endpointUrl: providerPayload.endpoint_url ?? "",
      modelName: providerPayload.model_name ?? "",
      credentialReference: providerPayload.credential_reference ?? "",
      monthlyTokenLimit: providerPayload.monthly_token_limit ?? PROVIDER_DRAFT_DEFAULT.monthlyTokenLimit,
      monthlyCostLimit: String(providerPayload.monthly_cost_limit ?? PROVIDER_DRAFT_DEFAULT.monthlyCostLimit),
      enabled: providerPayload.enabled ?? PROVIDER_DRAFT_DEFAULT.enabled,
    });
    setConnector(connectorPayload.enrollment ?? null);
  }

  useEffect(() => {
    let active = true;
    void refresh().catch((error: unknown) => {
      if (active) {
        setAiError(error instanceof Error ? error.message : "AI control data failed.");
      }
    });
    return () => {
      active = false;
    };
  }, []);

  async function saveProvider(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAiLoading("provider");
    setAiError(null);
    setAiMessage(null);
    try {
      const payload = await api<AIProviderConfig>("/api/v1/ai/provider", {
        method: "PATCH",
        body: {
          provider_name: providerDraft.providerName,
          endpoint_url: providerDraft.endpointUrl,
          model_name: providerDraft.modelName,
          credential_reference: providerDraft.credentialReference,
          monthly_token_limit: providerDraft.monthlyTokenLimit,
          monthly_cost_limit: providerDraft.monthlyCostLimit,
          enabled: providerDraft.enabled,
        },
      });
      setProvider(payload);
      setAiMessage("Provider configuration updated.");
    } catch (error: unknown) {
      setAiError(error instanceof Error ? error.message : "Provider save failed.");
    } finally {
      setAiLoading(null);
    }
  }

  async function saveConnector(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAiLoading("connector");
    setAiError(null);
    setAiMessage(null);
    try {
      const payload = await api<ConnectorEnrollment>("/api/v1/connectors/enrollment", {
        method: "POST",
        body: connectorDraft,
      });
      setConnector(payload);
      setAiMessage("Connector enrolled.");
    } catch (error: unknown) {
      setAiError(error instanceof Error ? error.message : "Connector save failed.");
    } finally {
      setAiLoading(null);
    }
  }

  async function revokeConnector() {
    setAiLoading("revoke");
    setAiError(null);
    setAiMessage(null);
    try {
      const payload = await api<ConnectorEnrollment>("/api/v1/connectors/revoke", {
        method: "POST",
        body: { reason: "Revoked from shell" },
      });
      setConnector(payload);
      setAiMessage("Connector revoked.");
    } catch (error: unknown) {
      setAiError(error instanceof Error ? error.message : "Connector revoke failed.");
    } finally {
      setAiLoading(null);
    }
  }

  return (
    <Panel eyebrow="AI & Connector" title="Provider and enrollment">
      {aiError ? <p className="status status-danger">{aiError}</p> : null}
      {aiMessage ? <p className="status status-success">{aiMessage}</p> : null}
      <form className="form-stack" onSubmit={saveProvider}>
        <div className="form-grid">
          <label>
            <span>Provider</span>
            <input
              value={providerDraft.providerName}
              onChange={(event) =>
                setProviderDraft((current) => ({ ...current, providerName: event.target.value }))
              }
            />
          </label>
          <label>
            <span>Model</span>
            <input
              value={providerDraft.modelName}
              onChange={(event) =>
                setProviderDraft((current) => ({ ...current, modelName: event.target.value }))
              }
            />
          </label>
        </div>
        <label>
          <span>Endpoint URL</span>
          <input
            value={providerDraft.endpointUrl}
            onChange={(event) =>
              setProviderDraft((current) => ({ ...current, endpointUrl: event.target.value }))
            }
          />
        </label>
        <label>
          <span>Credential reference</span>
          <input
            value={providerDraft.credentialReference}
            onChange={(event) =>
              setProviderDraft((current) => ({
                ...current,
                credentialReference: event.target.value,
              }))
            }
          />
        </label>
        <div className="form-grid">
          <label>
            <span>Monthly token limit</span>
            <input
              type="number"
              min="1"
              value={providerDraft.monthlyTokenLimit}
              onChange={(event) =>
                setProviderDraft((current) => ({
                  ...current,
                  monthlyTokenLimit: Number(event.target.value) || 1,
                }))
              }
            />
          </label>
          <label>
            <span>Monthly cost limit</span>
            <input
              value={providerDraft.monthlyCostLimit}
              onChange={(event) =>
                setProviderDraft((current) => ({
                  ...current,
                  monthlyCostLimit: event.target.value,
                }))
              }
            />
          </label>
        </div>
        <label>
          <input
            type="checkbox"
            checked={providerDraft.enabled}
            onChange={(event) =>
              setProviderDraft((current) => ({ ...current, enabled: event.target.checked }))
            }
          />{" "}
          Enabled
        </label>
        <button className="primary-button" type="submit" disabled={aiLoading === "provider"}>
          Save provider
        </button>
      </form>
      <form className="form-stack" onSubmit={saveConnector}>
        <div className="form-grid">
          <label>
            <span>Connector version</span>
            <input
              value={connectorDraft.connectorVersion}
              onChange={(event) =>
                setConnectorDraft((current) => ({
                  ...current,
                  connectorVersion: event.target.value,
                }))
              }
            />
          </label>
          <label>
            <span>Secret fingerprint</span>
            <input
              value={connectorDraft.sharedSecretFingerprint}
              onChange={(event) =>
                setConnectorDraft((current) => ({
                  ...current,
                  sharedSecretFingerprint: event.target.value,
                }))
              }
            />
          </label>
        </div>
        <div className="inline-actions">
          <button className="ghost-button" type="submit" disabled={aiLoading === "connector"}>
            Enroll connector
          </button>
          <button
            className="ghost-button"
            type="button"
            onClick={() => void revokeConnector()}
            disabled={aiLoading === "revoke" || !connector}
          >
            Revoke connector
          </button>
        </div>
      </form>
      <div className="notification-list">
        <div className="notification-item">
          <strong>{provider?.provider_name ?? "No provider configured"}</strong>
          <p>{provider?.model_name || "Model unset"}</p>
          <small>
            {provider?.enabled ? "enabled" : "disabled"} ·{" "}
            {provider?.monthly_token_limit ?? 0} tokens
          </small>
        </div>
        <div className="notification-item">
          <strong>{connector?.connector_version ?? "No connector enrolled"}</strong>
          <p>{connector?.health_status ?? "offline"}</p>
          <small>
            {connector?.status ?? "pending"} · {connector?.compatibility_window ?? "n/a"}
          </small>
        </div>
      </div>
    </Panel>
  );
}
