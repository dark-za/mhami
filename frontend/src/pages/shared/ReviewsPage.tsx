/** ReviewsPage — review queue, policy, AI criteria, and shadow summary. */

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../../api/client";
import type { Role } from "../../design-system/tokens";
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
  title: "",
  criteriaJson: "{}",
  referenceMediaNames: "",
  shadowMode: true,
  autoPassEnabled: false,
  autoPassRiskThreshold: 70,
};

export interface ReviewsPageProps {
  activeRole: Role | null;
}

export function ReviewsPage({ activeRole }: ReviewsPageProps) {
  const { t } = useTranslation();
  const isOwner = activeRole === "owner";
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
    const [dashboardPayload, queuePayload, policyPayload] =
      await Promise.all([
        api<ReviewDashboard>("/api/v1/reviews/dashboard"),
        api<QueueResponse>("/api/v1/reviews/queue"),
        api<ReviewPolicy>("/api/v1/reviews/policy"),
      ]);
    setDashboard(dashboardPayload);
    setQueue(queuePayload.items ?? []);
    setPolicy(policyPayload);
    if (isOwner) {
      const [criteriaPayload, shadowPayload] = await Promise.all([
        api<CriteriaResponse>("/api/v1/ai/criteria"),
        api<AIShadowSummary>("/api/v1/ai/shadow"),
      ]);
      setCriteria(criteriaPayload.criteria ?? []);
      setShadowSummary(shadowPayload);
    } else {
      setCriteria([]);
      setShadowSummary(null);
    }
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

  async function refreshAfterMutation(successMessage: string) {
    setReviewMessage(successMessage);
    try {
      await refresh();
    } catch {
      setReviewMessage(`${successMessage} ${t("reviews.refresh_notice")}`);
    }
  }

  useEffect(() => {
    let active = true;
    void refresh()
      .catch((_error: unknown) => {
        if (active) {
          setReviewError(t("reviews.load_failed"));
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
      await refreshAfterMutation(t("reviews.decision_saved"));
    } catch (_error: unknown) {
      setReviewError(t("reviews.decision_failed"));
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
      setReviewMessage(t("reviews.policy_updated"));
    } catch (_error: unknown) {
      setReviewError(t("reviews.policy_save_failed"));
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
      setReviewMessage(t("reviews.criteria_created"));
      setCriteriaDraft((current) => ({
        ...current,
        title: "",
        criteriaJson: "{}",
        referenceMediaNames: "",
      }));
    } catch (_error: unknown) {
      setReviewError(t("reviews.criteria_save_failed"));
    } finally {
      setReviewLoading(null);
    }
  }

  return (
    <Panel eyebrow={t("reviews.title")} title={t("reviews.workspace")}>
      {reviewError ? <p className="status status-danger">{reviewError}</p> : null}
      {reviewMessage ? <p className="status status-success">{reviewMessage}</p> : null}
      <div className="token-grid">
        <div className="token-swatch">
          <span>{t("reviews.completed_today")}</span>
          <strong>{dashboard?.summary.completed_today ?? 0}</strong>
        </div>
        <div className="token-swatch">
          <span>{t("reviews.overdue")}</span>
          <strong>{dashboard?.summary.overdue ?? 0}</strong>
        </div>
        <div className="token-swatch">
          <span>{t("reviews.quality_exceptions")}</span>
          <strong>{dashboard?.summary.quality_exceptions ?? 0}</strong>
        </div>
      </div>
      {isOwner ? <form className="form-stack" onSubmit={savePolicy}>
        <div className="form-grid">
          <label>
            <span>{t("reviews.score_visibility")}</span>
            <select
              value={policyDraft.employeeScoreVisibility}
              onChange={(event) =>
                setPolicyDraft((current) => ({
                  ...current,
                  employeeScoreVisibility: event.target.value,
                }))
              }
            >
              <option value="hidden">{t("reviews.visibility.hidden")}</option>
              <option value="summary">{t("reviews.visibility.summary")}</option>
              <option value="detailed">{t("reviews.visibility.detailed")}</option>
            </select>
          </label>
          <label>
            <span>{t("reviews.approved_task_weight_cap")}</span>
            <input
              type="number"
              className="bidi-ltr"
              dir="ltr"
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
          {t("reviews.historical_restatement")}
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
          {t("reviews.monitor_approval_required")}
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
          {t("reviews.restrict_sensitive_claims")}
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
          {t("reviews.extra_evidence_required")}
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
          {t("reviews.owner_alerts_enabled")}
        </label>
        <button className="primary-button" type="submit" disabled={reviewLoading === "policy"}>
          {t("reviews.save_policy")}
        </button>
      </form> : null}
      {isOwner ? <form className="form-stack" onSubmit={saveCriteria}>
        <div className="form-grid">
          <label>
            <span>{t("reviews.criteria_title")}</span>
            <input
              value={criteriaDraft.title}
              onChange={(event) =>
                setCriteriaDraft((current) => ({ ...current, title: event.target.value }))
              }
            />
          </label>
          <label>
            <span>{t("reviews.threshold")}</span>
            <input
              type="number"
              className="bidi-ltr"
              dir="ltr"
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
          <span>{t("reviews.criteria_json")}</span>
          <textarea
            className="bidi-ltr"
            dir="ltr"
            rows={4}
            value={criteriaDraft.criteriaJson}
            onChange={(event) =>
              setCriteriaDraft((current) => ({ ...current, criteriaJson: event.target.value }))
            }
          />
        </label>
        <label>
          <span>{t("reviews.reference_media_names")}</span>
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
          {t("reviews.shadow_mode")}
        </label>
        <label>
          <input
            type="checkbox"
            checked={criteriaDraft.autoPassEnabled}
            onChange={(event) =>
              setCriteriaDraft((current) => ({ ...current, autoPassEnabled: event.target.checked }))
            }
          />{" "}
          {t("reviews.auto_pass_enabled")}
        </label>
        <button className="ghost-button" type="submit" disabled={reviewLoading === "criteria"}>
          {t("reviews.create_criteria_version")}
        </button>
      </form> : null}
      {isOwner ? <div className="notification-list">
        {criteria.map((item) => (
          <div key={item.id} className="notification-item">
            <strong>
              v{item.version_number} · {item.title}
            </strong>
            <p>
              {item.shadow_mode ? t("reviews.mode_shadow") : t("reviews.mode_live")} · {t("reviews.auto_pass")} {item.auto_pass_enabled ? t("reviews.on") : t("reviews.off")}
            </p>
            <small>
              {t("reviews.threshold")} {item.auto_pass_risk_threshold} · {item.active ? t("reviews.active") : t("reviews.inactive")}
            </small>
          </div>
        ))}
      </div> : null}
      {isOwner && shadowSummary ? (
        <p className="muted">
          {t("reviews.shadow_agreement", { rate: shadowSummary.summary.agreement_rate, count: shadowSummary.summary.total_runs })}
        </p>
      ) : null}
      <div className="notification-list">
        {queue.map((item) => (
          <div key={item.id} className="notification-item">
            <strong>{item.title}</strong>
            <p>
              {t(`reviews.kind.${item.kind}`, { defaultValue: item.kind })} · {item.branch_name} · {t(`tasks.status.${item.status}`, { defaultValue: item.status })}
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
                    {t("reviews.retry")}
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "create_corrective_task")}
                    disabled={Boolean(reviewLoading)}
                  >
                    {t("reviews.corrective")}
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "mark_missed")}
                    disabled={Boolean(reviewLoading)}
                  >
                    {t("reviews.mark_missed")}
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "cancel")}
                    disabled={Boolean(reviewLoading)}
                  >
                    {t("reviews.cancel")}
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
                    {t("reviews.approve")}
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void submitDecision(item, "approve_despite_alert")}
                    disabled={Boolean(reviewLoading)}
                  >
                    {t("reviews.approve_despite_alert")}
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
                  {t("reviews.resolve")}
                </button>
              ) : null}
              <button
                className="ghost-button"
                type="button"
                onClick={() => void submitDecision(item, "override_restriction")}
                disabled={Boolean(reviewLoading)}
              >
                {t("reviews.override_restriction")}
              </button>
            </div>
          </div>
        ))}
        {queue.length === 0 ? <p className="muted">{t("reviews.empty")}</p> : null}
      </div>
      <div className="notification-list">
        {(dashboard?.branches ?? []).map((branch) => (
          <div key={branch.branch_id} className="notification-item">
            <strong>{branch.branch_name}</strong>
            <p>
              {t("reviews.branch_completed", { count: branch.completed_today })} · {t("reviews.branch_overdue", { count: branch.overdue })}
            </p>
            <small>{t("reviews.branch_quality_exceptions", { count: branch.quality_exceptions })}</small>
          </div>
        ))}
      </div>
      {policy ? (
        <p className="muted">
          {t("reviews.policy_summary", {
            visibility: t(`reviews.visibility.${policy.employee_score_visibility}`, { defaultValue: policy.employee_score_visibility }),
            alerts: policy.owner_alerts_enabled ? t("reviews.on") : t("reviews.off"),
          })}
        </p>
      ) : null}
    </Panel>
  );
}
