/** TasksPage — task list, transfer workflow, and run-action controls.

This panel owns the bottom of the "task lifecycle" funnel in the shell: claim,
start, complete, cancel, and the cross-company transfer flow.
*/

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../api/client";
import type { BootstrapState } from "../../api/bootstrap";
import { EmptyState, Panel, SkeletonBlock } from "../../shell/ui";
import type { TaskSummary, TaskTransferSummary } from "../../domain";

type MemberOption = {
  id: string;
  label: string;
  detail: string;
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

export function TasksPage({
  onTaskSelected,
  bootstrap,
}: {
  onTaskSelected?: (taskId: string) => void;
  bootstrap?: BootstrapState;
} = {}) {
  const [taskInstances, setTaskInstances] = useState<TaskSummary[]>([]);
  const [taskTransfers, setTaskTransfers] = useState<TaskTransferSummary[]>([]);
  const [memberOptions, setMemberOptions] = useState<MemberOption[]>([]);
  const [activeTaskId, setActiveTaskId] = useState("");
  const [taskError, setTaskError] = useState<string | null>(null);
  const [taskActionMessage, setTaskActionMessage] = useState<string | null>(null);
  const [taskActionLoading, setTaskActionLoading] = useState<string | null>(null);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [transferForm, setTransferForm] = useState({ taskId: "", requestedToId: "", reason: "" });
  const canManageTasks = bootstrap?.snapshot.currentUser.role === "owner" || bootstrap?.snapshot.currentUser.role === "monitor";

  async function refreshTasks() {
    setTasksLoading(true);
    const payload = await api<{ instances?: TaskSummary[] }>("/api/v1/tasks/instances");
    setTaskInstances(payload.instances ?? []);
    const instances = payload.instances ?? [];
    if (!activeTaskId && instances.length > 0) {
      const first = instances[0].id;
      setActiveTaskId(first);
      setTransferForm((current) => (current.taskId ? current : { ...current, taskId: first }));
      onTaskSelected?.(first);
    }
    setTaskError(null);
    setTasksLoading(false);
  }

  async function refreshTransfers() {
    const payload = await api<{ transfers?: TaskTransferSummary[] }>("/api/v1/tasks/transfers");
    setTaskTransfers(payload.transfers ?? []);
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
              "Team member",
            detail: membership.role ?? membership.login_id ?? "Active member",
          };
        })
        .filter((option) => option.id) ?? [];
    setMemberOptions(options);
  }

  useEffect(() => {
    let active = true;
    void refreshTasks().catch((error: unknown) => {
      if (active) {
        setTaskError(error instanceof Error ? error.message : "Tasks request failed.");
        setTasksLoading(false);
      }
    });
    void refreshTransfers().catch(() => undefined);
    void refreshMembers().catch(() => undefined);
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const transferRecipients = useMemo(() => {
    const byId = new Map<string, MemberOption>();
    const currentUser = bootstrap?.snapshot.currentUser;
    if (currentUser?.id) {
      byId.set(currentUser.id, {
        id: currentUser.id,
        label: currentUser.displayName || currentUser.loginId || "Current user",
        detail: currentUser.loginId,
      });
    }
    for (const option of memberOptions) {
      byId.set(option.id, option);
    }
    for (const instance of taskInstances) {
      if (instance.assigned_user && !byId.has(instance.assigned_user)) {
        byId.set(instance.assigned_user, {
          id: instance.assigned_user,
          label: "Assigned team member",
          detail: instance.name,
        });
      }
    }
    for (const transfer of taskTransfers) {
      if (transfer.requested_to && !byId.has(transfer.requested_to)) {
        byId.set(transfer.requested_to, {
          id: transfer.requested_to,
          label: "Previous transfer recipient",
          detail: transfer.status,
        });
      }
    }
    return Array.from(byId.values());
  }, [bootstrap, memberOptions, taskInstances, taskTransfers]);

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
        body: { reason: action === "cancel" ? "Cancelled from shell" : "" },
      });
      await refreshTasks();
      setTaskActionMessage(`Task ${action} succeeded.`);
    } catch (error: unknown) {
      setTaskError(error instanceof Error ? error.message : `${action} failed.`);
    } finally {
      setTaskActionLoading(null);
    }
  }

  async function submitTransfer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!transferForm.taskId || !transferForm.requestedToId) {
      setTaskError("Choose a task and a receiving team member.");
      return;
    }
    setTaskActionLoading(`transfer:${transferForm.taskId}`);
    setTaskError(null);
    try {
      await api(`/api/v1/tasks/instances/${transferForm.taskId}/transfers`, {
        method: "POST",
        body: { requested_to_id: transferForm.requestedToId, reason: transferForm.reason },
      });
      await refreshTransfers();
      setTaskActionMessage("Transfer request created.");
      setTransferForm({ taskId: "", requestedToId: "", reason: "" });
    } catch (error: unknown) {
      setTaskError(error instanceof Error ? error.message : "Transfer failed.");
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
      await refreshTransfers();
      setTaskActionMessage(`Transfer ${approved ? "approved" : "rejected"}.`);
    } catch (error: unknown) {
      setTaskError(error instanceof Error ? error.message : "Transfer resolution failed.");
    } finally {
      setTaskActionLoading(null);
    }
  }

  return (
    <Panel eyebrow="Task lifecycle" title="Tasks, transfers, and actions" variant="action">
      {taskError ? <p className="status status-danger">{taskError}</p> : null}
      {taskActionMessage ? <p className="status status-success">{taskActionMessage}</p> : null}

      {tasksLoading ? <SkeletonBlock rows={4} /> : null}

      {!tasksLoading && statusCounts.length > 0 ? (
        <div className="metric-strip" aria-label="Task status chart">
          {statusCounts.map((item) => {
            const width = `${Math.max(12, Math.round((item.count / taskInstances.length) * 100))}%`;
            return (
              <div key={item.status} className="metric-row">
                <span>{item.status}</span>
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
              {instance.status} · {instance.due_at}
            </p>
            <small>
              {instance.assigned_user ?? "unassigned"} · {instance.branch ?? "no branch"}
            </small>
            <div className="inline-actions">
              {(["claim", "start", "complete"] as const).map((action) => (
                <button
                  key={action}
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void runTaskAction(instance.id, action)}
                >
                  {action}
                </button>
              ))}
              {canManageTasks ? (
                <button
                  className="ghost-button"
                  type="button"
                  disabled={Boolean(taskActionLoading)}
                  onClick={() => void runTaskAction(instance.id, "cancel")}
                >
                  cancel
                </button>
              ) : null}
              <button
                className="ghost-button"
                type="button"
                onClick={() => {
                  setActiveTaskId(instance.id);
                  onTaskSelected?.(instance.id);
                }}
              >
                Open in evidence
              </button>
            </div>
          </div>
        ))}
        {!tasksLoading && taskInstances.length === 0 ? (
          <EmptyState title="No task instances" body="New work will appear here when schedules create tasks." />
        ) : null}
      </div>

      <form className="form-stack" onSubmit={submitTransfer}>
        <div className="form-grid">
          <label>
            <span>Task</span>
            <select
              value={transferForm.taskId}
              onChange={(event) =>
                setTransferForm((current) => ({ ...current, taskId: event.target.value }))
              }
            >
              <option value="">Select a task</option>
              {taskInstances.map((instance) => (
                <option key={instance.id} value={instance.id}>
                  {instance.name} · {instance.status}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Requested to</span>
            <select
              value={transferForm.requestedToId}
              onChange={(event) =>
                setTransferForm((current) => ({ ...current, requestedToId: event.target.value }))
              }
            >
              <option value="">Select a team member</option>
              {transferRecipients.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.label} · {member.detail}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          <span>Reason</span>
          <input
            value={transferForm.reason}
            onChange={(event) =>
              setTransferForm((current) => ({ ...current, reason: event.target.value }))
            }
          />
        </label>
        <button className="ghost-button" type="submit" disabled={Boolean(taskActionLoading)}>
          Request transfer
        </button>
      </form>

      <div className="notification-list">
        {taskTransfers.map((transfer) => (
          <div key={transfer.id} className="notification-item">
            <strong>{transfer.task_instance}</strong>
            <p>
              {transfer.status} · {transfer.requested_by} → {transfer.requested_to}
            </p>
            <small>{transfer.reason || "No reason provided"}</small>
            <div className="inline-actions">
              <button
                className="ghost-button"
                type="button"
                disabled={Boolean(taskActionLoading)}
                onClick={() => void resolveTransfer(transfer.id, true)}
              >
                Approve
              </button>
              <button
                className="ghost-button"
                type="button"
                disabled={Boolean(taskActionLoading)}
                onClick={() => void resolveTransfer(transfer.id, false)}
              >
                Reject
              </button>
            </div>
          </div>
        ))}
        {taskTransfers.length === 0 ? (
          <EmptyState title="No transfer requests" body="Pending transfers will appear here for review." />
        ) : null}
      </div>
    </Panel>
  );
}
