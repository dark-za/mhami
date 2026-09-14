/** AIControlPage — provider configuration and connector enrollment. */

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
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
    void refresh().catch((_error: unknown) => {
      if (active) {
        setAiError(t("ai_control.load_failed"));
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
      setAiMessage(t("ai_control.provider_updated"));
    } catch (_error: unknown) {
      setAiError(t("ai_control.provider_save_failed"));
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
      setAiMessage(t("ai_control.connector_enrolled"));
    } catch (_error: unknown) {
      setAiError(t("ai_control.connector_save_failed"));
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
      setAiMessage(t("ai_control.connector_revoked"));
    } catch (_error: unknown) {
      setAiError(t("ai_control.connector_revoke_failed"));
    } finally {
      setAiLoading(null);
    }
  }

  return (
    <Panel eyebrow={t("ai_control.eyebrow")} title={t("ai_control.title")}>
      {aiError ? <p className="status status-danger">{aiError}</p> : null}
      {aiMessage ? <p className="status status-success">{aiMessage}</p> : null}
      <form className="form-stack" onSubmit={saveProvider}>
        <div className="form-grid">
          <label>
            <span>{t("ai_control.provider")}</span>
            <input
              value={providerDraft.providerName}
              onChange={(event) =>
                setProviderDraft((current) => ({ ...current, providerName: event.target.value }))
              }
            />
          </label>
          <label>
            <span>{t("ai_control.model")}</span>
            <input
              value={providerDraft.modelName}
              onChange={(event) =>
                setProviderDraft((current) => ({ ...current, modelName: event.target.value }))
              }
            />
          </label>
        </div>
        <label>
          <span>{t("ai_control.endpoint_url")}</span>
          <input
            value={providerDraft.endpointUrl}
            onChange={(event) =>
              setProviderDraft((current) => ({ ...current, endpointUrl: event.target.value }))
            }
          />
        </label>
        <label>
          <span>{t("ai_control.credential_reference")}</span>
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
            <span>{t("ai_control.monthly_token_limit")}</span>
            <input
              type="number"
              className="bidi-ltr"
              dir="ltr"
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
            <span>{t("ai_control.monthly_cost_limit")}</span>
            <input
              value={providerDraft.monthlyCostLimit}
              className="bidi-ltr"
              dir="ltr"
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
          {t("ai_control.enabled")}
        </label>
        <button className="primary-button" type="submit" disabled={aiLoading === "provider"}>
          {t("ai_control.save_provider")}
        </button>
      </form>
      <form className="form-stack" onSubmit={saveConnector}>
        <div className="form-grid">
          <label>
            <span>{t("ai_control.connector_version")}</span>
            <input
              value={connectorDraft.connectorVersion}
              className="bidi-ltr"
              dir="ltr"
              onChange={(event) =>
                setConnectorDraft((current) => ({
                  ...current,
                  connectorVersion: event.target.value,
                }))
              }
            />
          </label>
          <label>
            <span>{t("ai_control.secret_fingerprint")}</span>
            <input
              value={connectorDraft.sharedSecretFingerprint}
              className="bidi-ltr"
              dir="ltr"
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
            {t("ai_control.enroll_connector")}
          </button>
          <button
            className="ghost-button"
            type="button"
            onClick={() => void revokeConnector()}
            disabled={aiLoading === "revoke" || !connector}
          >
            {t("ai_control.revoke_connector")}
          </button>
        </div>
      </form>
      <div className="notification-list">
        <div className="notification-item">
          <strong>{provider?.provider_name ?? t("ai_control.no_provider")}</strong>
          <p>{provider?.model_name || t("ai_control.model_unset")}</p>
          <small>
            {provider?.enabled ? t("ai_control.enabled_status") : t("ai_control.disabled_status")} · {provider?.monthly_token_limit ?? 0} {t("ai_control.tokens")}
          </small>
        </div>
        <div className="notification-item">
          <strong>{connector?.connector_version ?? t("ai_control.no_connector")}</strong>
          <p>{connector?.health_status ? t(`ai_control.connector_health.${connector.health_status}`, { defaultValue: connector.health_status }) : t("ai_control.offline")}</p>
          <small>
            {connector?.status ? t(`ai_control.connector_status.${connector.status}`, { defaultValue: connector.status }) : t("ai_control.pending")} · {connector?.compatibility_window ?? t("ai_control.not_available")}
          </small>
        </div>
      </div>
    </Panel>
  );
}
