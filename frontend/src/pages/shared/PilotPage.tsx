/** PilotPage — pilot program, weekly reports, issues, and change requests. */

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../api/client";
import { Panel } from "../../shell/ui";
import type {
  PilotChangeRequest,
  PilotDashboard,
  PilotIssue,
  PilotProgram,
  PilotReportView,
} from "../../domain";

interface ReportsResponse {
  reports?: PilotReportView[];
}
interface IssuesResponse {
  issues?: PilotIssue[];
}
interface ChangesResponse {
  change_requests?: PilotChangeRequest[];
}

const PROGRAM_DRAFT_DEFAULT = {
  status: "active",
  aiProviderName: "",
  connectorOwner: "",
  testEnvironment: "staging-equivalent",
};

const REPORT_DRAFT_DEFAULT = {
  weekEnding: "",
  metrics: "{}",
  errorAnalysis: "",
  capacityFindings: "",
};

const ISSUE_DRAFT_DEFAULT = { title: "", severity: "medium", details: "" };
const CHANGE_DRAFT_DEFAULT = { title: "", rationale: "" };

export function PilotPage() {
  const [program, setProgram] = useState<PilotProgram | null>(null);
  const [dashboard, setDashboard] = useState<PilotDashboard | null>(null);
  const [reports, setReports] = useState<PilotReportView[]>([]);
  const [issues, setIssues] = useState<PilotIssue[]>([]);
  const [changes, setChanges] = useState<PilotChangeRequest[]>([]);
  const [pilotError, setPilotError] = useState<string | null>(null);
  const [pilotMessage, setPilotMessage] = useState<string | null>(null);
  const [pilotLoading, setPilotLoading] = useState<string | null>(null);
  const [programDraft, setProgramDraft] = useState(PROGRAM_DRAFT_DEFAULT);
  const [reportDraft, setReportDraft] = useState(REPORT_DRAFT_DEFAULT);
  const [issueDraft, setIssueDraft] = useState(ISSUE_DRAFT_DEFAULT);
  const [changeDraft, setChangeDraft] = useState(CHANGE_DRAFT_DEFAULT);
  const [pilotStatusDraft, setPilotStatusDraft] = useState<Record<string, string>>({});

  async function refresh() {
    const [nextProgram, nextDashboard, reportsPayload, issuesPayload, changesPayload] =
      await Promise.all([
        api<PilotProgram>("/api/v1/pilot/program"),
        api<PilotDashboard>("/api/v1/pilot/dashboard"),
        api<ReportsResponse>("/api/v1/pilot/weekly-reports"),
        api<IssuesResponse>("/api/v1/pilot/issues"),
        api<ChangesResponse>("/api/v1/pilot/change-requests"),
      ]);
    setProgram(nextProgram);
    setProgramDraft({
      status: nextProgram.status ?? PROGRAM_DRAFT_DEFAULT.status,
      aiProviderName: nextProgram.ai_provider_name ?? "",
      connectorOwner: nextProgram.connector_owner ?? "",
      testEnvironment: nextProgram.test_environment ?? PROGRAM_DRAFT_DEFAULT.testEnvironment,
    });
    setDashboard(nextDashboard);
    setReports(reportsPayload.reports ?? []);
    setIssues(issuesPayload.issues ?? []);
    setChanges(changesPayload.change_requests ?? []);
  }

  useEffect(() => {
    let active = true;
    void refresh().catch((error: unknown) => {
      if (active) {
        setPilotError(error instanceof Error ? error.message : "Pilot data failed.");
      }
    });
    return () => {
      active = false;
    };
  }, []);

  async function saveProgram(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPilotLoading("program");
    setPilotError(null);
    setPilotMessage(null);
    try {
      const payload = await api<PilotProgram>("/api/v1/pilot/program", {
        method: "PATCH",
        body: {
          status: programDraft.status,
          ai_provider_name: programDraft.aiProviderName,
          connector_owner: programDraft.connectorOwner,
          test_environment: programDraft.testEnvironment,
        },
      });
      setProgram(payload);
      setPilotMessage("Pilot program updated.");
    } catch (error: unknown) {
      setPilotError(error instanceof Error ? error.message : "Pilot program save failed.");
    } finally {
      setPilotLoading(null);
    }
  }

  async function saveReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPilotLoading("report");
    setPilotError(null);
    setPilotMessage(null);
    try {
      const report = await api<PilotReportView>("/api/v1/pilot/weekly-reports", {
        method: "POST",
        body: {
          week_ending: reportDraft.weekEnding,
          metrics: JSON.parse(reportDraft.metrics || "{}"),
          error_analysis: reportDraft.errorAnalysis,
          capacity_findings: reportDraft.capacityFindings,
        },
      });
      setReports((current) => [report, ...current]);
      setPilotMessage("Weekly pilot report saved.");
    } catch (error: unknown) {
      setPilotError(error instanceof Error ? error.message : "Pilot report save failed.");
    } finally {
      setPilotLoading(null);
    }
  }

  async function saveIssue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPilotLoading("issue");
    setPilotError(null);
    setPilotMessage(null);
    try {
      const issue = await api<PilotIssue>("/api/v1/pilot/issues", {
        method: "POST",
        body: issueDraft,
      });
      setIssues((current) => [issue, ...current]);
      setPilotMessage("Pilot issue recorded.");
    } catch (error: unknown) {
      setPilotError(error instanceof Error ? error.message : "Pilot issue save failed.");
    } finally {
      setPilotLoading(null);
    }
  }

  async function saveChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPilotLoading("change");
    setPilotError(null);
    setPilotMessage(null);
    try {
      const change = await api<PilotChangeRequest>("/api/v1/pilot/change-requests", {
        method: "POST",
        body: changeDraft,
      });
      setChanges((current) => [change, ...current]);
      setPilotMessage("Pilot change request recorded.");
    } catch (error: unknown) {
      setPilotError(error instanceof Error ? error.message : "Pilot change save failed.");
    } finally {
      setPilotLoading(null);
    }
  }

  async function resolveIssue(issueId: string) {
    setPilotLoading(`issue:${issueId}`);
    setPilotError(null);
    setPilotMessage(null);
    try {
      const updated = await api<PilotIssue>(`/api/v1/pilot/issues/${issueId}`, {
        method: "PATCH",
        body: { status: pilotStatusDraft[issueId] ?? "resolved" },
      });
      setIssues((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setPilotMessage(`Issue marked ${updated.status}.`);
    } catch (error: unknown) {
      setPilotError(error instanceof Error ? error.message : "Pilot issue resolve failed.");
    } finally {
      setPilotLoading(null);
    }
  }

  async function decideChange(changeId: string, status: string) {
    setPilotLoading(`change:${changeId}:${status}`);
    setPilotError(null);
    setPilotMessage(null);
    try {
      const updated = await api<PilotChangeRequest>(
        `/api/v1/pilot/change-requests/${changeId}`,
        {
          method: "PATCH",
          body: { status },
        },
      );
      setChanges((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setPilotMessage(`Change request ${status}.`);
    } catch (error: unknown) {
      setPilotError(error instanceof Error ? error.message : "Pilot change decision failed.");
    } finally {
      setPilotLoading(null);
    }
  }

  return (
    <Panel eyebrow="Pilot" title="Program, weekly reports, and changes">
      {pilotError ? <p className="status status-danger">{pilotError}</p> : null}
      {pilotMessage ? <p className="status status-success">{pilotMessage}</p> : null}
      <form className="form-stack" onSubmit={saveProgram}>
        <div className="form-grid">
          <label>
            <span>Status</span>
            <input
              value={programDraft.status}
              onChange={(event) =>
                setProgramDraft((current) => ({ ...current, status: event.target.value }))
              }
            />
          </label>
          <label>
            <span>Test environment</span>
            <input
              value={programDraft.testEnvironment}
              onChange={(event) =>
                setProgramDraft((current) => ({
                  ...current,
                  testEnvironment: event.target.value,
                }))
              }
            />
          </label>
        </div>
        <div className="form-grid">
          <label>
            <span>AI provider</span>
            <input
              value={programDraft.aiProviderName}
              onChange={(event) =>
                setProgramDraft((current) => ({
                  ...current,
                  aiProviderName: event.target.value,
                }))
              }
            />
          </label>
          <label>
            <span>Connector owner</span>
            <input
              value={programDraft.connectorOwner}
              onChange={(event) =>
                setProgramDraft((current) => ({
                  ...current,
                  connectorOwner: event.target.value,
                }))
              }
            />
          </label>
        </div>
        <button className="primary-button" type="submit" disabled={pilotLoading === "program"}>
          Save pilot program
        </button>
      </form>
      <form className="form-stack" onSubmit={saveReport}>
        <div className="form-grid">
          <label>
            <span>Week ending</span>
            <input
              type="date"
              value={reportDraft.weekEnding}
              onChange={(event) =>
                setReportDraft((current) => ({ ...current, weekEnding: event.target.value }))
              }
            />
          </label>
          <label>
            <span>AI agreement rate</span>
            <input
              value={String(
                (program?.weekly_metrics_goal as Record<string, unknown> | undefined)?.[
                  "ai_agreement_rate"
                ] ?? "",
              )}
              readOnly
            />
          </label>
        </div>
        <label>
          <span>Metrics JSON</span>
          <textarea
            rows={3}
            value={reportDraft.metrics}
            onChange={(event) =>
              setReportDraft((current) => ({ ...current, metrics: event.target.value }))
            }
          />
        </label>
        <label>
          <span>Error analysis</span>
          <textarea
            rows={3}
            value={reportDraft.errorAnalysis}
            onChange={(event) =>
              setReportDraft((current) => ({ ...current, errorAnalysis: event.target.value }))
            }
          />
        </label>
        <label>
          <span>Capacity findings</span>
          <textarea
            rows={3}
            value={reportDraft.capacityFindings}
            onChange={(event) =>
              setReportDraft((current) => ({ ...current, capacityFindings: event.target.value }))
            }
          />
        </label>
        <button className="ghost-button" type="submit" disabled={pilotLoading === "report"}>
          Save weekly report
        </button>
      </form>
      <form className="form-stack" onSubmit={saveIssue}>
        <div className="form-grid">
          <label>
            <span>Issue title</span>
            <input
              value={issueDraft.title}
              onChange={(event) =>
                setIssueDraft((current) => ({ ...current, title: event.target.value }))
              }
            />
          </label>
          <label>
            <span>Severity</span>
            <input
              value={issueDraft.severity}
              onChange={(event) =>
                setIssueDraft((current) => ({ ...current, severity: event.target.value }))
              }
            />
          </label>
        </div>
        <label>
          <span>Details</span>
          <textarea
            rows={3}
            value={issueDraft.details}
            onChange={(event) =>
              setIssueDraft((current) => ({ ...current, details: event.target.value }))
            }
          />
        </label>
        <button className="ghost-button" type="submit" disabled={pilotLoading === "issue"}>
          Add issue
        </button>
      </form>
      <form className="form-stack" onSubmit={saveChange}>
        <label>
          <span>Change request title</span>
          <input
            value={changeDraft.title}
            onChange={(event) =>
              setChangeDraft((current) => ({ ...current, title: event.target.value }))
            }
          />
        </label>
        <label>
          <span>Rationale</span>
          <textarea
            rows={3}
            value={changeDraft.rationale}
            onChange={(event) =>
              setChangeDraft((current) => ({ ...current, rationale: event.target.value }))
            }
          />
        </label>
        <button className="ghost-button" type="submit" disabled={pilotLoading === "change"}>
          Add change request
        </button>
      </form>
      <div className="token-grid">
        <div className="token-swatch">
          <span>Branches target</span>
          <strong>{program?.branch_count_target ?? 0}</strong>
        </div>
        <div className="token-swatch">
          <span>Employees target</span>
          <strong>{program?.employee_count_target ?? 0}</strong>
        </div>
        <div className="token-swatch">
          <span>Chrome devices</span>
          <strong>{program?.chrome_device_count ?? 0}</strong>
        </div>
      </div>
      <div className="notification-list">
        {reports.map((report) => (
          <div key={report.id} className="notification-item">
            <strong>{report.week_ending}</strong>
            <p>AI agreement {report.ai_agreement_rate}%</p>
            <small>{report.error_analysis || "No error analysis"}</small>
          </div>
        ))}
        {issues.map((issue) => (
          <div key={issue.id} className="notification-item">
            <strong>{issue.title}</strong>
            <p>
              {issue.severity} · {issue.status}
            </p>
            <small>{issue.details || "No details"}</small>
            <div className="action-row">
              <input
                value={pilotStatusDraft[issue.id] ?? "resolved"}
                onChange={(event) =>
                  setPilotStatusDraft((current) => ({ ...current, [issue.id]: event.target.value }))
                }
                aria-label={`Status for ${issue.title}`}
              />
              <button
                className="ghost-button"
                type="button"
                disabled={pilotLoading === `issue:${issue.id}`}
                onClick={() => void resolveIssue(issue.id)}
              >
                Resolve
              </button>
            </div>
          </div>
        ))}
        {changes.map((change) => (
          <div key={change.id} className="notification-item">
            <strong>{change.title}</strong>
            <p>{change.status}</p>
            <small>{change.rationale || "No rationale"}</small>
            <div className="action-row">
              <button
                className="ghost-button"
                type="button"
                disabled={pilotLoading === `change:${change.id}:approved`}
                onClick={() => void decideChange(change.id, "approved")}
              >
                Approve
              </button>
              <button
                className="ghost-button"
                type="button"
                disabled={pilotLoading === `change:${change.id}:rejected`}
                onClick={() => void decideChange(change.id, "rejected")}
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
      {dashboard ? (
        <p className="muted">
          Weekly evidence: {String(dashboard.summary["evidence_items_week"] ?? 0)} · AI runs:{" "}
          {String(dashboard.summary["ai_runs_week"] ?? 0)} · Connector:{" "}
          {String(dashboard.summary["connector_status"] ?? "offline")}
        </p>
      ) : null}
    </Panel>
  );
}
