/** PeoplePage — owner-managed people, branches, job roles, and branch access. */

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../api/client";
import type { BootstrapState } from "../../api/bootstrap";
import { EmptyState, Panel, SkeletonBlock } from "../../shell/ui";
import { roleLabels } from "../../design-system/tokens";

type Member = {
  user?: string;
  user_id?: string;
  login_id?: string;
  display_name?: string;
  role?: string;
  active?: boolean;
};

type Branch = {
  id: string;
  name: string;
  code: string;
  timezone: string;
  operational_day_cutoff: string;
  active: boolean;
};

type JobRole = {
  id: string;
  name: string;
  code: string;
  active: boolean;
};

export interface PeoplePageProps {
  bootstrap: BootstrapState;
  activeRole: BootstrapState["snapshot"]["currentUser"]["role"];
}

const DEFAULT_BRANCH = {
  name: "",
  code: "",
  timezone: "Asia/Riyadh",
  operational_day_cutoff: "03:00:00",
};

export function PeoplePage({ bootstrap, activeRole }: PeoplePageProps) {
  const { company, currentUser } = bootstrap.snapshot;
  const [members, setMembers] = useState<Member[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [jobRoles, setJobRoles] = useState<JobRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [memberDraft, setMemberDraft] = useState({
    login_id: "",
    display_name: "",
    password: "",
    role: "employee",
  });
  const [branchDraft, setBranchDraft] = useState(DEFAULT_BRANCH);
  const [jobRoleDraft, setJobRoleDraft] = useState({ name: "", code: "" });
  const [assignmentDraft, setAssignmentDraft] = useState({
    user_id: "",
    branch_id: "",
    job_role_id: "",
    membership_type: "primary",
  });

  const isOwner = activeRole === "owner" || activeRole === "platform_admin";
  const activeMembers = useMemo(() => members.filter((member) => member.active !== false), [members]);

  async function refresh() {
    const [memberPayload, branchPayload, rolePayload] = await Promise.all([
      api<{ memberships?: Member[] }>("/api/v1/auth/company/members"),
      api<{ branches?: Branch[] }>("/api/v1/organizations/branches"),
      api<{ roles?: JobRole[] }>("/api/v1/organizations/job-roles"),
    ]);
    const nextMembers = memberPayload.memberships ?? [];
    const nextBranches = branchPayload.branches ?? [];
    const nextRoles = rolePayload.roles ?? [];
    setMembers(nextMembers);
    setBranches(nextBranches);
    setJobRoles(nextRoles);
    setAssignmentDraft((current) => ({
      ...current,
      user_id: current.user_id || nextMembers[0]?.user_id || nextMembers[0]?.user || "",
      branch_id: current.branch_id || nextBranches[0]?.id || "",
      job_role_id: current.job_role_id || nextRoles[0]?.id || "",
    }));
  }

  useEffect(() => {
    let active = true;
    void refresh()
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "People data failed to load.");
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

  async function createMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("member");
    setError(null);
    setMessage(null);
    try {
      await api("/api/v1/auth/company/users", { method: "POST", body: memberDraft });
      setMemberDraft({ login_id: "", display_name: "", password: "", role: "employee" });
      await refresh();
      setMessage("Company user created.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "User creation failed.");
    } finally {
      setSaving(null);
    }
  }

  async function createBranch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("branch");
    setError(null);
    setMessage(null);
    try {
      await api("/api/v1/organizations/branches", { method: "POST", body: branchDraft });
      setBranchDraft(DEFAULT_BRANCH);
      await refresh();
      setMessage("Branch created.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Branch creation failed.");
    } finally {
      setSaving(null);
    }
  }

  async function createJobRole(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("job-role");
    setError(null);
    setMessage(null);
    try {
      await api("/api/v1/organizations/job-roles", { method: "POST", body: jobRoleDraft });
      setJobRoleDraft({ name: "", code: "" });
      await refresh();
      setMessage("Job role created.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Job role creation failed.");
    } finally {
      setSaving(null);
    }
  }

  async function assignBranch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving("assignment");
    setError(null);
    setMessage(null);
    try {
      await api("/api/v1/auth/company/branch-memberships", {
        method: "POST",
        body: assignmentDraft,
      });
      await refresh();
      setMessage("Branch access assigned.");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Branch assignment failed.");
    } finally {
      setSaving(null);
    }
  }

  return (
    <Panel eyebrow="People" title="Company people and access">
      {error ? <p className="status status-danger">{error}</p> : null}
      {message ? <p className="status status-success">{message}</p> : null}
      {loading ? <SkeletonBlock rows={5} /> : null}

      <div className="token-grid">
        <div className="token-swatch">
          <span>Company</span>
          <strong>{company.name}</strong>
        </div>
        <div className="token-swatch">
          <span>Active session</span>
          <strong>{currentUser.displayName || currentUser.loginId}</strong>
        </div>
        <div className="token-swatch">
          <span>Role</span>
          <strong>{activeRole ? roleLabels[activeRole].en : "Signed out"}</strong>
        </div>
      </div>

      {!loading ? (
        <>
          <div className="notification-list">
            {activeMembers.map((member) => (
              <div key={member.user_id ?? member.user} className="notification-item">
                <strong>{member.display_name || member.login_id || member.user}</strong>
                <p>{member.login_id || "login id unavailable"}</p>
                <small>{member.role || "role unset"}</small>
              </div>
            ))}
            {activeMembers.length === 0 ? (
              <EmptyState title="No members" body="Members created by the owner will appear here." />
            ) : null}
          </div>

          {isOwner ? (
            <>
              <form className="form-stack" onSubmit={createMember}>
                <h3>Create company user</h3>
                <div className="form-grid">
                  <label>
                    <span>Login ID</span>
                    <input
                      required
                      value={memberDraft.login_id}
                      onChange={(event) => setMemberDraft((current) => ({ ...current, login_id: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>Display name</span>
                    <input
                      value={memberDraft.display_name}
                      onChange={(event) => setMemberDraft((current) => ({ ...current, display_name: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>Password</span>
                    <input
                      required
                      type="password"
                      value={memberDraft.password}
                      onChange={(event) => setMemberDraft((current) => ({ ...current, password: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>Platform role</span>
                    <select
                      value={memberDraft.role}
                      onChange={(event) => setMemberDraft((current) => ({ ...current, role: event.target.value }))}
                    >
                      <option value="employee">Employee</option>
                      <option value="monitor">Monitor</option>
                      <option value="owner">Owner</option>
                    </select>
                  </label>
                </div>
                <button className="primary-button" type="submit" disabled={saving === "member"}>
                  Create user
                </button>
              </form>

              <form className="form-stack" onSubmit={createBranch}>
                <h3>Create branch</h3>
                <div className="form-grid">
                  <label>
                    <span>Name</span>
                    <input
                      required
                      value={branchDraft.name}
                      onChange={(event) => setBranchDraft((current) => ({ ...current, name: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>Code</span>
                    <input
                      required
                      value={branchDraft.code}
                      onChange={(event) => setBranchDraft((current) => ({ ...current, code: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>Timezone</span>
                    <input
                      required
                      value={branchDraft.timezone}
                      onChange={(event) => setBranchDraft((current) => ({ ...current, timezone: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>Operational cutoff</span>
                    <input
                      required
                      type="time"
                      step="1"
                      value={branchDraft.operational_day_cutoff}
                      onChange={(event) =>
                        setBranchDraft((current) => ({ ...current, operational_day_cutoff: event.target.value }))
                      }
                    />
                  </label>
                </div>
                <button className="ghost-button" type="submit" disabled={saving === "branch"}>
                  Create branch
                </button>
              </form>

              <form className="form-stack" onSubmit={createJobRole}>
                <h3>Create job role</h3>
                <div className="form-grid">
                  <label>
                    <span>Name</span>
                    <input
                      required
                      value={jobRoleDraft.name}
                      onChange={(event) => setJobRoleDraft((current) => ({ ...current, name: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>Code</span>
                    <input
                      required
                      value={jobRoleDraft.code}
                      onChange={(event) => setJobRoleDraft((current) => ({ ...current, code: event.target.value }))}
                    />
                  </label>
                </div>
                <button className="ghost-button" type="submit" disabled={saving === "job-role"}>
                  Create job role
                </button>
              </form>

              <form className="form-stack" onSubmit={assignBranch}>
                <h3>Assign branch access</h3>
                <div className="form-grid">
                  <label>
                    <span>User</span>
                    <select
                      required
                      value={assignmentDraft.user_id}
                      onChange={(event) => setAssignmentDraft((current) => ({ ...current, user_id: event.target.value }))}
                    >
                      <option value="">Select user</option>
                      {activeMembers.map((member) => (
                        <option key={member.user_id ?? member.user} value={member.user_id ?? member.user}>
                          {member.display_name || member.login_id || member.user}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Branch</span>
                    <select
                      required
                      value={assignmentDraft.branch_id}
                      onChange={(event) => setAssignmentDraft((current) => ({ ...current, branch_id: event.target.value }))}
                    >
                      <option value="">Select branch</option>
                      {branches.map((branch) => (
                        <option key={branch.id} value={branch.id}>
                          {branch.name} - {branch.code}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Job role</span>
                    <select
                      required
                      value={assignmentDraft.job_role_id}
                      onChange={(event) => setAssignmentDraft((current) => ({ ...current, job_role_id: event.target.value }))}
                    >
                      <option value="">Select job role</option>
                      {jobRoles.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.name} - {role.code}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <button className="primary-button" type="submit" disabled={saving === "assignment"}>
                  Assign branch
                </button>
              </form>
            </>
          ) : (
            <p className="muted">Management actions are available to the company owner only.</p>
          )}
        </>
      ) : null}
    </Panel>
  );
}
