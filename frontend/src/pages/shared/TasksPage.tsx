/** TasksPage — task list, transfer workflow, and run-action controls.

This panel owns the bottom of the "task lifecycle" funnel in the shell: claim,
start, complete, cancel, and the cross-company transfer flow.
*/

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../api/client";
import { Panel } from "../../shell/ui";
import type { TaskSummary, TaskTransferSummary } from "../../domain";

export function TasksPage({ onTaskSelected }: { onTaskSelected?: (taskId: string) => void } = {}) {
  const [taskInstances, setTaskInstances] = useState<TaskSummary[]>([]);
  const [taskTransfers, setTaskTransfers] = useState<TaskTransferSummary[]>([]);
  const [activeTaskId, setActiveTaskId] = useState("");
  const [taskError, setTaskError] = useState<string | null>(null);
  const [taskActionMessage, setTaskActionMessage] = useState<string | null>(null);
  const [taskActionLoading, setTaskActionLoading] = useState<string | null>(null);
  const [transferForm, setTransferForm] = useState({ taskId: "", requestedToId: "", reason: "" });

  async function refreshTasks() {
    const payload = await api<{ instances?: TaskSummary[] }>("/api/v1/tasks/instances");
    setTaskInstances(payload.instances ?? []);
    if (!activeTaskId && (payload.instances ?? []).length > 0) {
      const first = (payload.instances ?? [])[0].id;
      setActiveTaskId(first);
      onTaskSelected?.(first);
    }
    setTaskError(null);
  }

  async function refreshTransfers() {
    const payload = await api<{ transfers?: TaskTransferSummary[] }>("/api/v1/tasks/transfers");
    setTaskTransfers(payload.transfers ?? []);
  }

  useEffect(() => {
    let active = true;
    void refreshTasks().catch((error: unknown) => {
      if (active) {
        setTaskError(error instanceof Error ? error.message : "Tasks request failed.");
      }
    });
    void refreshTransfers().catch(() => undefined);
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      setTaskError("Task ID and requested-to user ID are required.");
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
    <Panel eyebrow="Task lifecycle" title="Tasks, transfers, and actions">
      {taskError ? <p className="status status-danger">{taskError}</p> : null}
      {taskActionMessage ? <p className="status status-success">{taskActionMessage}</p> : null}
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
              {(["claim", "start", "complete", "cancel"] as const).map((action) => (
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
        {taskInstances.length === 0 ? <p className="muted">No task instances.</p> : null}
      </div>

      <form className="form-stack" onSubmit={submitTransfer}>
        <div className="form-grid">
          <label>
            <span>Task ID</span>
            <input
              value={transferForm.taskId}
              onChange={(event) =>
                setTransferForm((current) => ({ ...current, taskId: event.target.value }))
              }
            />
          </label>
          <label>
            <span>Requested to (user ID)</span>
            <input
              value={transferForm.requestedToId}
              onChange={(event) =>
                setTransferForm((current) => ({ ...current, requestedToId: event.target.value }))
              }
            />
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
        {taskTransfers.length === 0 ? <p className="muted">No transfer requests.</p> : null}
      </div>
    </Panel>
  );
}
