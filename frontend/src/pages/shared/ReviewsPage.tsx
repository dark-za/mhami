/** ReviewsPage — review queue, policy, AI criteria, and shadow summary. */

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../api/client";
import { Panel } from "../../shell/ui";
import type {
  AICriterionSummary,
  AIShadowSummary,
  ReviewDashboard,
  ReviewPolicy,
  ReviewQueueItem,
} from "../../domain";

interface QueueResponse {
  items?: ReviewQueueItem[];
}

interface CriteriaResponse {
  criteria?: AICriterionSummary[];
}

const POLICY_DRAFT_DEFAULT = {
  employeeScoreVisibility: "summary",
  historicalReportRestatement: false,
  monitorApprovalRequired: true,
  sensitiveTaskClaimRestricted: true,
  extraEvidenceRequired: false,
  ownerAlertsEnabled: true,
  approvedTaskWeightCap: 5,
};

const CRITERIA_DRAFT_DEFAULT = {
  title: "Shadow criteria",
  criteriaJson: "{}",
  referenceMediaNames: "",
  shadowMode: true,
  autoPassEnabled: false,
  autoPassRiskThreshold: 70,
};

export function ReviewsPage() {
  const [dashboard, setDashboard] = useState<ReviewDashboard | null>(null);
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [policy, setPolicy] = useState<ReviewPolicy | null>(null);
  const [policyDraft, setPolicyDraft] = useState(POLICY_DRAFT_DEFAULT);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewMessage, setReviewMessage] = useState<string | null>(null);
  const [reviewLoading, setReviewLoading] = useState<string | null>(null);
  const [criteria, setCriteria] = useState<AICriterionSummary[]>([]);
  const [shadowSummary, setShadowSummary] = useState<AIShadowSummary | null>(null);
  const [criteriaDraft, setCriteriaDraft] = useState(CRITERIA_DRAFT_DEFAULT);

  async function refresh() {
    const [dashboardPayload, queuePayload, policyPayload, criteriaPayload, shadowPayload] =
      await Promise.all([
        api<ReviewDashboard>("/api/v1/reviews/dashboard"),
        api<QueueResponse>("/api/v1/reviews/queue"),
        api<ReviewPolicy>("/api/v1/reviews/policy"),
        api<CriteriaResponse>("/api/v1/ai/criteria"),
        api<AIShadowSummary>("/api/v1/ai/shadow"),
      ]);
    setDashboard(dashboardPayload);
    setQueue(queuePayload.items ?? []);
    setPolicy(policyPayload);
    setCriteria(criteriaPayload.criteria ?? []);
    setShadowSummary(shadowPayload);
    setPolicyDraft({
      employeeScoreVisibility: policyPayload.employee_score_visibility ?? "summary",
      historicalReportRestatement: policyPayload.historical_report_restatement ?? false,
      monitorApprovalRequired: policyPayload.monitor_approval_required ?? true,
      sensitiveTaskClaimRestricted: policyPayload.sensitive_task_claim_restricted ?? true,
      extraEvidenceRequired: policyPayload.extra_evidence_required ?? false,
      ownerAlertsEnabled: policyPayload.owner_alerts_enabled ?? true,
      approvedTaskWeightCap: policyPayload.approved_task_weight_cap ?? 5,
    });
  }

  useEffect(() => {
    let active = true;
    void refresh()
      .catch((error: unknown) => {
        if (active) {
          setReviewError(error instanceof Error ? error.message : "Review data failed.");
        }
      })
      .finally(() => {
        if (active) {
          setReviewLoading(null);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function submitDecision(item: ReviewQueueItem, decisionType: string) {
    setReviewLoading(`${item.id}:${decisionType}`);
    setReviewError(null);
    setReviewMessage(null);
    try {
      await api("/api/v1/reviews/decisions", {
        method: "POST",
        body: {
          decision_type: decisionType,
          reason: item.reason,
          task_instance_id: item.task_instance_id,
          evidence_item_id: item.evidence_item_id,
          issue_report_id: item.issue_report_id,
        },
      });
      await refresh();
      setReviewMessage("Decision saved.");
    } catch (error: unknown) {
      setReviewError(error instanceof Error ? error.message : "Review decision failed.");
    } finally {
      setReviewLoading(null);
    }
  }

  async function savePolicy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setReviewLoading("policy");
    setReviewError(null);
    setReviewMessage(null);
    try {
      const payload = await api<ReviewPolicy>("/api/v1/reviews/policy", {
        method: "PATCH",
        body: {
          employee_score_visibility: policyDraft.employeeScoreVisibility,
          historical_report_restatement: policyDraft.historicalReportRestatement,
          monitor_approval_required: policyDraft.monitorApprovalRequired,
          sensitive_task_claim_restricted: policyDraft.sensitiveTaskClaimRestricted,
          extra_evidence_required: policyDraft.extraEvidenceRequired,
          owner_alerts_enabled: policyDraft.ownerAlertsEnabled,
          approved_task_weight_cap: policyDraft.approvedTaskWeightCap,
        },
      });
      setPolicy(payload);
      setReviewMessage("Policy updated.");
    } catch (error: unknown) {
      setReviewError(error instanceof Error ? error.message : "Policy save failed.");
    } finally {
      setReviewLoading(null);
    }
  }

  async function saveCriteria(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setReviewLoading("criteria");
    setReviewError(null);
    setReviewMessage(null);
    try {
      const payload = await api<AICriterionSummary>("/api/v1/ai/criteria", {
        method: "POST",
        body: {
          title: criteriaDraft.title,
          criteria_json: JSON.parse(criteriaDraft.criteriaJson || "{}"),
          reference_media_names: criteriaDraft.referenceMediaNames
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean),
          shadow_mode: criteriaDraft.shadowMode,
          auto_pass_enabled: criteriaDraft.autoPassEnabled,
          auto_pass_risk_threshold: criteriaDraft.autoPassRiskThreshold,
        },
      });
      setCriteria((current) => [payload, ...current]);
      setReviewMessage("AI criteria version created.");
      setCriteriaDraft((current) => ({
        ...current,
        title: "",
        criteriaJson: "{}",
        referenceMediaNames: "",
      }));
    } catch (error: unknown) {
      setReviewError(error instanceof Error ? error.message : "Criteria save failed.");
    } finally {
      setReviewLoading(null);
    }
  }

  return (
    <Panel eyebrow="Reviews" title="Queue, policy, and AI criteria">
      {reviewError ? <p className="status status-danger">{reviewError}</p> : null}
      {reviewMessage ? <p className="status status-success">{reviewMessage}</p> : null}
      <div className="token-grid">
        <div className="token-swatch">
          <span>Completed today</span>
          <strong>{dashboard?.summary.completed_today ?? 0}</strong>
        </div>
        <div className="token-swatch">
          <span>Overdue</span>
          <strong>{dashboard?.summary.overdue ?? 0}</strong>
        </div>
        <div className="token-swatch">
          <span>Quality exceptions</span>
          <strong>{dashboard?.summary.quality_exceptions ?? 0}</strong>
        </div>
      </div>
      <form className="form-stack" onSubmit={savePolicy}>
        <div className="form-grid">
          <label>
            <span>Score visibility</span>
            <select
              value={policyDraft.employeeScoreVisibility}
              onChange={(event) =>
                setPolicyDraft((current) => ({
                  ...current,
                  employeeScoreVisibility: event.target.value,
                }))
              }
            >
              <option value="hidden">Hidden</option>
              <option value="summary">Summary</option>
              <option value="detailed">Detailed</option>
            </select>
          </label>
          <label>
            <span>Approved task weight cap</span>
            <input
              type="number"
              min="1"
              value={policyDraft.approvedTaskWeightCap}
              onChange={(event) =>
                setPolicyDraft((current) => ({
                  ...current,
                  approvedTaskWeightCap: Number(event.target.value) || 1,
                }))
              }
            />
          </label>
        </div>
        <label>
          <input
            type="checkbox"
            checked={policyDraft.historicalReportRestatement}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                historicalReportRestatement: event.target.checked,
              }))
            }
          />{" "}
          Historical restatement
        </label>
        <label>
          <input
            type="checkbox"
            checked={policyDraft.monitorApprovalRequired}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                monitorApprovalRequired: event.target.checked,
              }))
            }
          />{" "}
          Monitor approval required
        </label>
        <label>
          <input
            type="checkbox"
            checked={policyDraft.sensitiveTaskClaimRestricted}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                sensitiveTaskClaimRestricted: event.target.checked,
              }))
            }
          />{" "}
          Restrict sensitive claims
        </label>
        <label>
          <input
            type="checkbox"
            checked={policyDraft.extraEvidenceRequired}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                extraEvidenceRequired: event.target.checked,
              }))
            }
          />{" "}
          Extra evidence required
        </label>
        <label>
          <input
            type="checkbox"
            checked={policyDraft.ownerAlertsEnabled}
            onChange={(event) =>
              setPolicyDraft((current) => ({
                ...current,
                ownerAlertsEnabled: event.target.checked,
              }))
            }
          />{" "}
          Owner alerts enabled
        </label>
        <button className="primary-button" type="submit" disabled={reviewLoading === "policy"}>
          Save policy
        </button>
      </form>
      <form className="form-stack" onSubmit={saveCriteria}>
        <div className="form-grid">
          <label>
            <span>Criteria title</span>
            <input
              value={criteriaDraft.title}
              onChange={(event) =>
                setCriteriaDraft((current) => ({ ...current, title: event.target.value }))
              }
            />
          </label>
          <label>
            <span>Threshold</span>
            <input
              type="number"
              min="1"
              max="100"
              value={criteriaDraft.autoPassRiskThreshold}
              onChange={(event) =>
                setCriteriaDraft((current) => ({
                  ...current,
                  autoPassRiskThreshold: Number(event.target.value) || 70,
                }))
              }
            />
          </label>
        </div>
        <label>
          <span>Criteria JSON</span>
          <textarea
            rows={4}
            value={criteriaDraft.criteriaJson}
            onChange={(event) =>
              setCriteriaDraft((current) => ({ ...current, criteriaJson: event.target.value }))
            }
          />
        </label>
        <label>
          <span>Reference media names</span>
          <input
            value={criteriaDraft.referenceMediaNames}
            onChange={(event) =>
              setCriteriaDraft((current) => ({
                ...current,
                referenceMediaNames: event.target.value,
              }))
            }
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={criteriaDraft.shadowMode}
            onChange={(event) =>
              setCriteriaDraft((current) => ({ ...current, shadowMode: event.target.checked }))
            }
          />{" "}
          Shadow mode
        </label>
        <label>
          <input
            type="checkbox"
            checked={criteriaDraft.autoPassEnabled}
            onChange={(event) =>
              setCriteriaDraft((current) => ({ ...current, autoPassEnabled: event.target.checked }))
            }
          />{" "}
          Auto-pass enabled
        </label>
        <button className="ghost-button" type="submit" disabled={reviewLoading === "criteria"}>
          Create criteria version
        </button>
      </form>
      <div className="notification-list">
        {criteria.map((item) => (
          <div key={item.id} className="notification-item">
            <strong>
              v{item.version_number} · {item.title}
            </strong>
            <p>
              {item.shadow_mode ? "Shadow" : "Live"} · Auto-pass{" "}
              {item.auto_pass_enabled ? "on" : "off"}
            </p>
            <small>
              Threshold {item.auto_pass_risk_threshold} ·{" "}
              {item.active ? "active" : "inactive"}
            </small>
          </div>
        ))}
      </div>
      {shadowSummary ? (
        <p className="muted">
          Shadow agreement {shadowSummary.summary.agreement_rate}% over{" "}
          {shadowSummary.summary.total_runs} runs.
        </p>
      ) : null}
      <div className="notification-list">
        {queue.map((item) => (
          <div key={item.id} className="notification-item">
            <strong>{item.title}</strong>
            <p>
              {item.kind} · {item.branch_name} · {item.status}
            </p>
            <small>{item.reason}</small>
            <div className="inline-actions">
              {item.kind === "task" ? (
                <>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "retry_same_task")}
                    disabled={Boolean(reviewLoading)}
                  >
                    Retry
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "create_corrective_task")}
                    disabled={Boolean(reviewLoading)}
                  >
                    Corrective
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "mark_missed")}
                    disabled={Boolean(reviewLoading)}
                  >
                    Mark missed
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "cancel")}
                    disabled={Boolean(reviewLoading)}
                  >
                    Cancel
                  </button>
                </>
              ) : null}
              {item.kind === "evidence" ? (
                <>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "approve")}
                    disabled={Boolean(reviewLoading)}
                  >
                    Approve
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "approve_despite_alert")}
                    disabled={Boolean(reviewLoading)}
                  >
                    Approve despite alert
                  </button>
                </>
              ) : null}
              {item.kind === "issue" ? (
                <button
                  className="ghost-button"
                  type="button"
                  onClick={() => void submitDecision(item, "approve")}
                  disabled={Boolean(reviewLoading)}
                >
                  Resolve
                </button>
              ) : null}
              <button
                className="ghost-button"
                type="button"
                onClick={() => void submitDecision(item, "override_restriction")}
                disabled={Boolean(reviewLoading)}
              >
                Override restriction
              </button>
            </div>
          </div>
        ))}
        {queue.length === 0 ? <p className="muted">No review items.</p> : null}
      </div>
      <div className="notification-list">
        {(dashboard?.branches ?? []).map((branch) => (
          <div key={branch.branch_id} className="notification-item">
            <strong>{branch.branch_name}</strong>
            <p>
              Completed {branch.completed_today} · Overdue {branch.overdue}
            </p>
            <small>Quality exceptions {branch.quality_exceptions}</small>
          </div>
        ))}
      </div>
      {policy ? (
        <p className="muted">
          Score visibility: {policy.employee_score_visibility} · Alerts:{" "}
          {policy.owner_alerts_enabled ? "on" : "off"}
        </p>
      ) : null}
    </Panel>
  );
}
