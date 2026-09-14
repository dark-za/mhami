/** TasksPage — task list, transfer workflow, and run-action controls.

This panel owns the bottom of the "task lifecycle" funnel in the shell: claim,
start, complete, cancel, and the cross-company transfer flow.
*/

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";

import { api } from "../../api/client";
import type { BootstrapState } from "../../api/bootstrap";
import { EmptyState, Panel, SkeletonBlock } from "../../shell/ui";
import type { TaskSummary, TaskTransferSummary } from "../../domain";

type MemberOption = {
  id: string;
  label: string;
  detail: string;
};

type TransferRecipient = {
  id: string;
  display_name: string;
};

type BranchOption = {
  id: string;
  name: string;
};

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

type TaskRequest = {
  id: string;
  task_instance?: string | null;
  requested_by: string;
  requested_to?: string | null;
  kind: string;
  reason: string;
  status: string;
  decision_reason?: string;
};

function formatDate(value: string | null | undefined, locale: string): string {
  if (!value) return "";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString(locale);
}

export function TasksPage({
  onTaskSelected,
  bootstrap,
}: {
  onTaskSelected?: (taskId: string) => void;
  bootstrap?: BootstrapState;
} = {}) {
  const { i18n, t } = useTranslation();
  const navigate = useNavigate();
  const [taskInstances, setTaskInstances] = useState<TaskSummary[]>([]);
  const [taskTransfers, setTaskTransfers] = useState<TaskTransferSummary[]>([]);
  const [taskRequests, setTaskRequests] = useState<TaskRequest[]>([]);
  const [memberOptions, setMemberOptions] = useState<MemberOption[]>([]);
  const [transferRecipients, setTransferRecipients] = useState<TransferRecipient[]>([]);
  const [activeTaskId, setActiveTaskId] = useState("");
  const [taskError, setTaskError] = useState<string | null>(null);
  const [taskActionMessage, setTaskActionMessage] = useState<string | null>(null);
  const [taskActionLoading, setTaskActionLoading] = useState<string | null>(null);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [transferForm, setTransferForm] = useState({ taskId: "", requestedToId: "", reason: "" });
  const [taskDefinition, setTaskDefinition] = useState({
    name: "",
    instructions: "",
    branchId: "",
    assignedUserId: "",
    recurrenceType: "daily_fixed",
    scheduledTime: "09:00",
  });
  const [requestForm, setRequestForm] = useState({ taskId: "", branchId: "", kind: "unable_to_complete", reason: "" });
  const canManageTasks = bootstrap?.snapshot.currentUser.role === "owner" || bootstrap?.snapshot.currentUser.role === "monitor";
  const visibleBranches = (bootstrap?.branchScope ?? []) as unknown as BranchOption[];

  async function refreshTasks() {
    setTasksLoading(true);
    const payload = await api<{ instances?: TaskSummary[] }>("/api/v1/tasks/instances");
    setTaskInstances(payload.instances ?? []);
    const instances = payload.instances ?? [];
    const transferTaskId = activeTaskId || instances[0]?.id || "";
    if (!activeTaskId && instances.length > 0) {
      const first = instances[0].id;
      setActiveTaskId(first);
      setTransferForm((current) => (current.taskId ? current : { ...current, taskId: first }));
      onTaskSelected?.(first);
    }
    void refreshTransferRecipients(transferTaskId).catch(() => undefined);
    setTaskError(null);
    setTasksLoading(false);
  }

  async function refreshTransfers() {
    const payload = await api<{ transfers?: TaskTransferSummary[] }>("/api/v1/tasks/transfers");
    setTaskTransfers(payload.transfers ?? []);
  }

  async function refreshRequests() {
    const payload = await api<{ requests?: TaskRequest[] }>("/api/v1/tasks/requests");
    setTaskRequests(payload.requests ?? []);
  }

  async function refreshMembers() {
    const payload = await api<MembersPayload>("/api/v1/auth/company/members");
    const options =
      payload.memberships
        ?.filter((membership) => membership.active !== false)
        .map((membership) => {
          const id = membership.user_id ?? membership.user ?? "";
          const knownCurrentUser = bootstrap?.snapshot.currentUser.id === id;
          return {
            id,
            label:
              membership.display_name ??
              (knownCurrentUser ? bootstrap?.snapshot.currentUser.displayName : undefined) ??
              membership.login_id ??
              t("tasks.team_member"),
            detail: membership.role ?? membership.login_id ?? "active",
          };
        })
        .filter((option) => option.id) ?? [];
    setMemberOptions(options);
  }

  async function refreshTransferRecipients(taskId: string) {
    if (!taskId) {
      setTransferRecipients([]);
      return;
    }
    const payload = await api<{ recipients?: TransferRecipient[] }>(
      `/api/v1/tasks/transfer-recipients?task_instance_id=${encodeURIComponent(taskId)}`,
    );
    setTransferRecipients(payload.recipients ?? []);
  }

  async function refreshAfterMutation(
    refreshers: Array<() => Promise<void>>,
    successMessage: string,
  ) {
    setTaskActionMessage(successMessage);
    const results = await Promise.allSettled(refreshers.map((refresher) => refresher()));
    if (results.some((result) => result.status === "rejected")) {
      setTaskActionMessage(`${successMessage} ${t("tasks.refresh_notice")}`);
    }
  }

  useEffect(() => {
    let active = true;
    void refreshTasks().catch((_error: unknown) => {
      if (active) {
        setTaskError(t("tasks.load_failed"));
        setTasksLoading(false);
      }
    });
    void refreshTransfers().catch(() => undefined);
    void refreshRequests().catch(() => undefined);
    void refreshMembers().catch(() => undefined);
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const statusCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const instance of taskInstances) {
      const status = instance.status ?? "unknown";
      counts.set(status, (counts.get(status) ?? 0) + 1);
    }
    return Array.from(counts.entries()).map(([status, count]) => ({ status, count }));
  }, [taskInstances]);

  async function runTaskAction(
    instanceId: string,
    action: "claim" | "start" | "complete" | "cancel",
  ) {
    setTaskActionLoading(`${instanceId}:${action}`);
    setTaskActionMessage(null);
    setTaskError(null);
    try {
      await api(`/api/v1/tasks/instances/${instanceId}/${action}`, {
        method: "POST",
      body: { reason: action === "cancel" ? "cancelled_from_workspace" : "" },
      });
      await refreshAfterMutation(
        [refreshTasks],
        t("tasks.action_succeeded", { action: t(`tasks.action.${action}`) }),
      );
    } catch (_error: unknown) {
      setTaskError(t("tasks.action_failed", { action: t(`tasks.action.${action}`) }));
    } finally {
      setTaskActionLoading(null);
    }
  }

  async function submitTransfer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!transferForm.taskId || !transferForm.requestedToId) {
      setTaskError(t("tasks.transfer_missing_fields"));
      return;
    }
    setTaskActionLoading(`transfer:${transferForm.taskId}`);
    setTaskError(null);
    try {
      await api(`/api/v1/tasks/instances/${transferForm.taskId}/transfers`, {
        method: "POST",
        body: { requested_to_id: transferForm.requestedToId, reason: transferForm.reason },
      });
      await refreshAfterMutation([refreshTransfers, refreshTasks], t("tasks.transfer_created"));
      setTransferForm({ taskId: "", requestedToId: "", reason: "" });
    } catch (_error: unknown) {
      setTaskError(t("tasks.transfer_failed"));
    } finally {
      setTaskActionLoading(null);
    }
  }

  async function resolveTransfer(transferId: string, approved: boolean) {
    setTaskActionLoading(`${transferId}:${approved ? "approve" : "reject"}`);
    setTaskError(null);
    try {
      await api(`/api/v1/tasks/transfers/${transferId}/resolve`, {
        method: "POST",
        body: { approved },
      });
      await refreshAfterMutation(
        [refreshTransfers],
        t("tasks.transfer_resolved", { decision: t(`tasks.decision.${approved ? "approved" : "rejected"}`) }),
      );
    } catch (_error: unknown) {
      setTaskError(t("tasks.transfer_resolution_failed"));
    } finally {
      setTaskActionLoading(null);
    }
  }

  async function createScheduledTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!taskDefinition.name || !taskDefinition.instructions || !taskDefinition.branchId || !taskDefinition.assignedUserId) {
      setTaskError(t("tasks.creation_missing_fields"));
      return;
    }
    setTaskActionLoading("task-definition");
    setTaskError(null);
    try {
      await api("/api/v1/tasks/scheduled-tasks", {
        method: "POST",
        body: {
          branch_id: taskDefinition.branchId,
          name: taskDefinition.name,
          assigned_user_id: taskDefinition.assignedUserId,
          instructions: taskDefinition.instructions,
          recurrence_type: taskDefinition.recurrenceType,
          scheduled_time: taskDefinition.scheduledTime || null,
        },
      });
      setTaskDefinition((current) => ({ ...current, name: "", instructions: "" }));
      await refreshAfterMutation([refreshTasks], t("tasks.creation_success"));
    } catch (_error: unknown) {
      setTaskError(t("tasks.creation_failed"));
    } finally {
      setTaskActionLoading(null);
    }
  }

  async function submitTaskRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const task = taskInstances.find((item) => item.id === requestForm.taskId);
    const branchId = task?.branch ?? requestForm.branchId;
    if (!branchId || !requestForm.reason || (requestForm.kind !== "task_suggestion" && !task)) {
      setTaskError(t("tasks.request_missing_fields"));
      return;
    }
    setTaskActionLoading("task-request");
    setTaskError(null);
    try {
      await api("/api/v1/tasks/requests", {
        method: "POST",
        body: {
          branch_id: branchId,
          task_instance_id: task?.id ?? null,
          kind: requestForm.kind,
          reason: requestForm.reason,
        },
      });
      setRequestForm({ taskId: "", branchId: "", kind: "unable_to_complete", reason: "" });
      await refreshAfterMutation([refreshRequests], t("tasks.request_created"));
    } catch (_error: unknown) {
      setTaskError(t("tasks.request_failed"));
    } finally {
      setTaskActionLoading(null);
    }
  }

  async function resolveTaskRequest(taskRequestId: string, approved: boolean) {
    setTaskActionLoading(`${taskRequestId}:${approved ? "approve" : "reject"}`);
    setTaskError(null);
    try {
      await api(`/api/v1/tasks/requests/${taskRequestId}/resolve`, { method: "POST", body: { approved } });
      await refreshAfterMutation(
        [refreshRequests, refreshTasks, refreshTransfers],
        t("tasks.request_resolved", { decision: t(`tasks.decision.${approved ? "approved" : "rejected"}`) }),
      );
    } catch (_error: unknown) {
      setTaskError(t("tasks.request_resolution_failed"));
    } finally {
      setTaskActionLoading(null);
    }
  }

  return (
    <Panel eyebrow={t("tasks.lifecycle")} title={t("tasks.workspace")} variant="action">
      {taskError ? <p className="status status-danger">{taskError}</p> : null}
      {taskActionMessage ? <p className="status status-success">{taskActionMessage}</p> : null}

      {tasksLoading ? <SkeletonBlock rows={4} /> : null}

      {!tasksLoading && statusCounts.length > 0 ? (
        <div className="metric-strip" aria-label={t("tasks.status_chart")}>
          {statusCounts.map((item) => {
            const width = `${Math.max(12, Math.round((item.count / taskInstances.length) * 100))}%`;
            return (
              <div key={item.status} className="metric-row">
                <span>{t(`tasks.status.${item.status}`, { defaultValue: item.status })}</span>
                <div className="metric-track">
                  <span className="metric-bar" style={{ width }} />
                </div>
                <strong>{item.count}</strong>
              </div>
            );
          })}
        </div>
      ) : null}

      <div className="notification-list">
        {taskInstances.map((instance) => (
          <div key={instance.id} className="notification-item">
            <strong>{instance.name}</strong>
            <p>
              {t(`tasks.status.${instance.status}`, { defaultValue: instance.status })} · {formatDate(instance.due_at, i18n.language)}
            </p>
            <small>
              {instance.assigned_user_name || t("tasks.unassigned")} · {instance.branch_name || t("tasks.no_branch")}
            </small>
            <div className="inline-actions">
              {canManageTasks && ["pending", "overdue"].includes(instance.status ?? "") ? (
                <button
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void runTaskAction(instance.id, "claim")}
                >
                  {t("tasks.action.claim")}
                </button>
              ) : null}
              {["pending", "claimed", "overdue"].includes(instance.status ?? "") ? (
                <button
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void runTaskAction(instance.id, "start")}
                >
                  {t("tasks.action.start")}
                </button>
              ) : null}
              {["claimed", "in_progress", "overdue"].includes(instance.status ?? "") ? (
                <button
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void runTaskAction(instance.id, "complete")}
                >
                  {t("tasks.action.complete")}
                </button>
              ) : null}
              {canManageTasks && ["pending", "claimed", "in_progress", "overdue"].includes(instance.status ?? "") ? (
                <button
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void runTaskAction(instance.id, "cancel")}
                >
                  {t("tasks.action.cancel")}
                </button>
              ) : null}
              <button
                className="ghost-button"
                type="button"
                onClick={() => {
                  setActiveTaskId(instance.id);
                  onTaskSelected?.(instance.id);
                  navigate("/evidence");
                }}
              >
                {t("tasks.open_evidence")}
              </button>
            </div>
          </div>
        ))}
        {!tasksLoading && taskInstances.length === 0 ? (
          <EmptyState title={t("tasks.no_instances")} body={t("tasks.no_instances_body")} />
        ) : null}
      </div>

      {canManageTasks ? (
        <form className="form-stack" onSubmit={createScheduledTask}>
          <h3>{t("tasks.create_scheduled")}</h3>
          <div className="form-grid">
            <label><span>{t("tasks.name")}</span><input required value={taskDefinition.name} onChange={(event) => setTaskDefinition((current) => ({ ...current, name: event.target.value }))} /></label>
            <label><span>{t("tasks.branch")}</span><select required value={taskDefinition.branchId} onChange={(event) => setTaskDefinition((current) => ({ ...current, branchId: event.target.value }))}><option value="">{t("tasks.select_branch")}</option>{visibleBranches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label>
            <label><span>{t("tasks.employee")}</span><select required value={taskDefinition.assignedUserId} onChange={(event) => setTaskDefinition((current) => ({ ...current, assignedUserId: event.target.value }))}><option value="">{t("tasks.select_employee")}</option>{memberOptions.filter((member) => member.detail === "employee").map((member) => <option key={member.id} value={member.id}>{member.label}</option>)}</select></label>
            <label><span>{t("tasks.repeat")}</span><select value={taskDefinition.recurrenceType} onChange={(event) => setTaskDefinition((current) => ({ ...current, recurrenceType: event.target.value }))}><option value="daily_fixed">{t("tasks.recurrence.daily")}</option><option value="weekly_fixed">{t("tasks.recurrence.weekly")}</option></select></label>
            <label>
              <span>{t("tasks.scheduled_time")}</span>
              <input
                type="time"
                className="bidi-ltr"
                dir="ltr"
                required
                value={taskDefinition.scheduledTime}
                onInput={(event) => {
                  const scheduledTime = event.currentTarget.value;
                  setTaskDefinition((current) => ({ ...current, scheduledTime }));
                }}
                onChange={(event) => {
                  const scheduledTime = event.currentTarget.value;
                  setTaskDefinition((current) => ({ ...current, scheduledTime }));
                }}
              />
            </label>
          </div>
          <label><span>{t("tasks.instructions")}</span><textarea required value={taskDefinition.instructions} onChange={(event) => setTaskDefinition((current) => ({ ...current, instructions: event.target.value }))} /></label>
          <button className="primary-button" type="submit" disabled={Boolean(taskActionLoading)}>{t("tasks.create_task")}</button>
        </form>
      ) : (
        <form className="form-stack" onSubmit={submitTaskRequest}>
          <h3>{t("tasks.request_change")}</h3>
          <div className="form-grid">
            <label><span>{t("tasks.task")}</span><select required={requestForm.kind !== "task_suggestion"} value={requestForm.taskId} onChange={(event) => setRequestForm((current) => ({ ...current, taskId: event.target.value }))}><option value="">{requestForm.kind === "task_suggestion" ? t("tasks.no_existing_task") : t("tasks.select_your_task")}</option>{taskInstances.map((instance) => <option key={instance.id} value={instance.id}>{instance.name} · {t(`tasks.status.${instance.status}`, { defaultValue: instance.status })}</option>)}</select></label>
            {requestForm.kind === "task_suggestion" ? <label><span>{t("tasks.branch")}</span><select required value={requestForm.branchId} onChange={(event) => setRequestForm((current) => ({ ...current, branchId: event.target.value }))}><option value="">{t("tasks.select_branch")}</option>{visibleBranches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label> : null}
            <label><span>{t("tasks.request_type")}</span><select value={requestForm.kind} onChange={(event) => setRequestForm((current) => ({ ...current, kind: event.target.value, taskId: event.target.value === "task_suggestion" ? "" : current.taskId }))}><option value="unable_to_complete">{t("tasks.request_kind.unable_to_complete")}</option><option value="cancellation">{t("tasks.request_kind.cancellation")}</option><option value="task_suggestion">{t("tasks.request_kind.task_suggestion")}</option></select></label>
          </div>
          <label><span>{t("tasks.reason")}</span><textarea required value={requestForm.reason} onChange={(event) => setRequestForm((current) => ({ ...current, reason: event.target.value }))} /></label>
          <button className="ghost-button" type="submit" disabled={Boolean(taskActionLoading)}>{t("tasks.send_request")}</button>
        </form>
      )}

      <form className="form-stack" onSubmit={submitTransfer}>
        <div className="form-grid">
          <label>
            <span>{t("tasks.task")}</span>
            <select
              value={transferForm.taskId}
              onChange={(event) => {
                const taskId = event.target.value;
                setTransferForm((current) => ({ ...current, taskId, requestedToId: "" }));
                void refreshTransferRecipients(taskId);
              }}
            >
              <option value="">{t("tasks.select_task")}</option>
              {taskInstances.map((instance) => (
                <option key={instance.id} value={instance.id}>
                  {instance.name} · {t(`tasks.status.${instance.status}`, { defaultValue: instance.status })}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>{t("tasks.requested_to")}</span>
            <select
              value={transferForm.requestedToId}
              onChange={(event) =>
                setTransferForm((current) => ({ ...current, requestedToId: event.target.value }))
              }
            >
              <option value="">{t("tasks.select_team_member")}</option>
              {transferRecipients.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.display_name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          <span>{t("tasks.reason")}</span>
          <input
            value={transferForm.reason}
            onChange={(event) =>
              setTransferForm((current) => ({ ...current, reason: event.target.value }))
            }
          />
        </label>
        <button className="ghost-button" type="submit" disabled={Boolean(taskActionLoading)}>
          {t("tasks.request_transfer")}
        </button>
      </form>

      <div className="notification-list">
        {taskTransfers.map((transfer) => (
          <div key={transfer.id} className="notification-item">
            <strong>{transfer.task_name || t("tasks.transfer")}</strong>
            <p>
              {t(`tasks.status.${transfer.status}`, { defaultValue: transfer.status })} · {transfer.requested_by_name || t("tasks.requester")} → {transfer.requested_to_name || t("tasks.recipient")}
            </p>
            <small>{transfer.reason || t("tasks.no_reason")}</small>
            {canManageTasks && transfer.status === "pending" ? (
              <div className="inline-actions">
                <button
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void resolveTransfer(transfer.id, true)}
                >
                  {t("tasks.decision.approve")}
                </button>
                <button
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void resolveTransfer(transfer.id, false)}
                >
                  {t("tasks.decision.reject")}
                </button>
              </div>
            ) : null}
          </div>
        ))}
        {taskTransfers.length === 0 ? (
          <EmptyState title={t("tasks.no_transfers")} body={t("tasks.no_transfers_body")} />
        ) : null}
      </div>

      <div className="notification-list">
        {taskRequests.map((taskRequest) => (
          <div key={taskRequest.id} className="notification-item">
            <strong>{t(`tasks.request_kind.${taskRequest.kind}`, { defaultValue: taskRequest.kind })}</strong>
            <p>{t(`tasks.status.${taskRequest.status}`, { defaultValue: taskRequest.status })} · {taskRequest.task_instance ?? t("tasks.general_suggestion")}</p>
            <small>{taskRequest.reason}</small>
            {canManageTasks && taskRequest.status === "pending" ? (
              <div className="inline-actions">
                <button className="ghost-button" type="button" disabled={Boolean(taskActionLoading)} onClick={() => void resolveTaskRequest(taskRequest.id, true)}>{t("tasks.decision.approve")}</button>
                <button className="ghost-button" type="button" disabled={Boolean(taskActionLoading)} onClick={() => void resolveTaskRequest(taskRequest.id, false)}>{t("tasks.decision.reject")}</button>
              </div>
            ) : null}
          </div>
        ))}
        {taskRequests.length === 0 ? <EmptyState title={t("tasks.no_requests")} body={t("tasks.no_requests_body")} /> : null}
      </div>
    </Panel>
  );
}
