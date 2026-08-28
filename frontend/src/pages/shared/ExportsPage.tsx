/** ExportsPage — export policy and request flow. */

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../api/client";
import { Panel } from "../../shell/ui";
import type { ExportPolicy, ExportRequestItem } from "../../domain";

interface RequestsResponse {
  requests?: ExportRequestItem[];
}

const POLICY_DRAFT_DEFAULT = {
  futureNotificationBoundaries: "emails,chat",
  externalStorageBoundaries: "none",
  providerReviewChecklist: "support approval,scope check",
};

const REQUEST_DRAFT_DEFAULT = {
  exportType: "csv",
  branchIds: "",
  categories: "tasks,evidence",
  startDate: "",
  endDate: "",
};

export function ExportsPage() {
  const [policy, setPolicy] = useState<ExportPolicy | null>(null);
  const [requests, setRequests] = useState<ExportRequestItem[]>([]);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState<string | null>(null);
  const [policyDraft, setPolicyDraft] = useState(POLICY_DRAFT_DEFAULT);
  const [requestDraft, setRequestDraft] = useState(REQUEST_DRAFT_DEFAULT);

  async function refresh() {
    const [policyPayload, requestsPayload] = await Promise.all([
      api<ExportPolicy>("/api/v1/exports/policy"),
      api<RequestsResponse>("/api/v1/exports/requests/list"),
    ]);
    setPolicy(policyPayload);
    setPolicyDraft({
      futureNotificationBoundaries: policyPayload.future_notification_boundaries.join(","),
      externalStorageBoundaries: policyPayload.external_storage_boundaries.join(","),
      providerReviewChecklist: policyPayload.provider_review_checklist.join(","),
    });
    setRequests(requestsPayload.requests ?? []);
  }

  useEffect(() => {
    let active = true;
    void refresh().catch((error: unknown) => {
      if (active) {
        setExportError(error instanceof Error ? error.message : "Export data failed.");
      }
    });
    return () => {
      active = false;
    };
  }, []);

  async function savePolicy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setExportLoading("policy");
    setExportError(null);
    setExportMessage(null);
    try {
      const payload = await api<ExportPolicy>("/api/v1/exports/policy", {
        method: "PATCH",
        body: {
          future_notification_boundaries: policyDraft.futureNotificationBoundaries
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean),
          external_storage_boundaries: policyDraft.externalStorageBoundaries
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean),
          provider_review_checklist: policyDraft.providerReviewChecklist
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean),
        },
      });
      setPolicy(payload);
      setExportMessage("Export policy updated.");
    } catch (error: unknown) {
      setExportError(error instanceof Error ? error.message : "Policy update failed.");
    } finally {
      setExportLoading(null);
    }
  }

  async function createExport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setExportLoading("request");
    setExportError(null);
    setExportMessage(null);
    try {
      const payload = await api<ExportRequestItem>("/api/v1/exports/requests", {
        method: "POST",
        body: {
          export_type: requestDraft.exportType,
          branch_ids: requestDraft.branchIds
            ? requestDraft.branchIds.split(",").map((value) => value.trim()).filter(Boolean)
            : [],
          categories: requestDraft.categories.split(",").map((value) => value.trim()).filter(Boolean),
          start_date: requestDraft.startDate || undefined,
          end_date: requestDraft.endDate || undefined,
        },
      });
      setRequests((current) => [payload, ...current]);
      setExportMessage("Export generated.");
    } catch (error: unknown) {
      setExportError(error instanceof Error ? error.message : "Export request failed.");
    } finally {
      setExportLoading(null);
    }
  }

  return (
    <Panel eyebrow="Exports" title="Policy and download requests">
      {exportError ? <p className="status status-danger">{exportError}</p> : null}
      {exportMessage ? <p className="status status-success">{exportMessage}</p> : null}
      <form className="form-stack" onSubmit={savePolicy}>
        <label>
          <span>Future notification boundaries</span>
          <input
            value={policyDraft.futureNotificationBoundaries}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                futureNotificationBoundaries: event.target.value,
              }))
            }
          />
        </label>
        <label>
          <span>External storage boundaries</span>
          <input
            value={policyDraft.externalStorageBoundaries}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                externalStorageBoundaries: event.target.value,
              }))
            }
          />
        </label>
        <label>
          <span>Provider review checklist</span>
          <input
            value={policyDraft.providerReviewChecklist}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                providerReviewChecklist: event.target.value,
              }))
            }
          />
        </label>
        <button className="primary-button" type="submit" disabled={exportLoading === "policy"}>
          Save export policy
        </button>
      </form>
      <form className="form-stack" onSubmit={createExport}>
        <div className="form-grid">
          <label>
            <span>Export type</span>
            <select
              value={requestDraft.exportType}
              onChange={(event) =>
                setRequestDraft((current) => ({ ...current, exportType: event.target.value }))
              }
            >
              <option value="csv">CSV</option>
              <option value="zip">ZIP</option>
              <option value="pdf">PDF</option>
            </select>
          </label>
          <label>
            <span>Branch IDs</span>
            <input
              value={requestDraft.branchIds}
              onChange={(event) =>
                setRequestDraft((current) => ({ ...current, branchIds: event.target.value }))
              }
              placeholder="Leave empty for accessible branches"
            />
          </label>
        </div>
        <label>
          <span>Categories</span>
          <input
            value={requestDraft.categories}
            onChange={(event) =>
              setRequestDraft((current) => ({ ...current, categories: event.target.value }))
            }
          />
        </label>
        <div className="form-grid">
          <label>
            <span>Start date</span>
            <input
              type="date"
              value={requestDraft.startDate}
              onChange={(event) =>
                setRequestDraft((current) => ({ ...current, startDate: event.target.value }))
              }
            />
          </label>
          <label>
            <span>End date</span>
            <input
              type="date"
              value={requestDraft.endDate}
              onChange={(event) =>
                setRequestDraft((current) => ({ ...current, endDate: event.target.value }))
              }
            />
          </label>
        </div>
        <button className="ghost-button" type="submit" disabled={exportLoading === "request"}>
          Create export
        </button>
      </form>
      <div className="notification-list">
        {requests.map((request) => (
          <div key={request.id} className="notification-item">
            <strong>{request.export_type.toUpperCase()}</strong>
            <p>
              {request.status} · expires {request.expires_at}
            </p>
            <small>{request.categories.join(", ") || "all categories"}</small>
            <div className="inline-actions">
              <a
                className="ghost-button"
                href={`/api/v1/exports/download/${request.download_token}`}
              >
                Download
              </a>
            </div>
          </div>
        ))}
        {requests.length === 0 ? <p className="muted">No exports yet.</p> : null}
      </div>
      {policy ? (
        <p className="muted">
          Boundary policy loaded for {policy.future_notification_boundaries.length} notification
          targets.
        </p>
      ) : null}
    </Panel>
  );
}
