/** PeoplePage — owner-managed people, branches, job roles, and branch access. */

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../../api/client";
import { fetchBootstrap, type BootstrapState } from "../../api/bootstrap";
import { EmptyState, Panel, SkeletonBlock } from "../../shell/ui";

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
  const { t } = useTranslation();
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
    branch_id: "",
    job_role_id: "",
  });
  const [branchDraft, setBranchDraft] = useState(DEFAULT_BRANCH);
  const [jobRoleDraft, setJobRoleDraft] = useState({ name: "", code: "" });
  const [assignmentDraft, setAssignmentDraft] = useState({
    user_id: "",
    branch_id: "",
    job_role_id: "",
    membership_type: "primary",
  });

  const isOwner = activeRole === "owner";
  const canManagePeople = isOwner || activeRole === "monitor";
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
    setMemberDraft((current) => ({
      ...current,
      branch_id: current.branch_id || nextBranches[0]?.id || "",
      job_role_id: current.job_role_id || nextRoles[0]?.id || "",
    }));
  }

  async function refreshAfterMutation(successMessage: string) {
    const [peopleResult, bootstrapResult] = await Promise.allSettled([refresh(), fetchBootstrap()]);
    if (bootstrapResult.status === "fulfilled") {
      window.dispatchEvent(new CustomEvent("mhami.bootstrap.refreshed", { detail: bootstrapResult.value }));
    }
    const refreshFailed = peopleResult.status === "rejected" || bootstrapResult.status === "rejected";
    setMessage(refreshFailed ? `${successMessage} ${t("people.refresh_notice")}` : successMessage);
  }

  useEffect(() => {
    let active = true;
    void refresh()
      .catch((_caught: unknown) => {
        if (active) {
          setError(t("people.load_failed"));
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
      const { branch_id, job_role_id, ...account } = memberDraft;
      await api("/api/v1/auth/company/users", {
        method: "POST",
        body: isOwner ? account : { ...account, branch_id, job_role_id },
      });
      setMemberDraft((current) => ({
        ...current,
        login_id: "",
        display_name: "",
        password: "",
        role: "employee",
      }));
      await refreshAfterMutation(t("people.user_created"));
    } catch (_caught: unknown) {
      setError(t("people.user_create_failed"));
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
      await refreshAfterMutation(t("people.branch_created"));
    } catch (_caught: unknown) {
      setError(t("people.branch_create_failed"));
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
      await refreshAfterMutation(t("people.job_role_created"));
    } catch (_caught: unknown) {
      setError(t("people.job_role_create_failed"));
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
      await refreshAfterMutation(t("people.branch_assigned"));
    } catch (_caught: unknown) {
      setError(t("people.branch_assignment_failed"));
    } finally {
      setSaving(null);
    }
  }

  return (
    <Panel eyebrow={t("people.title")} title={t("people.workspace")}>
      {error ? <p className="status status-danger">{error}</p> : null}
      {message ? <p className="status status-success">{message}</p> : null}
      {loading ? <SkeletonBlock rows={5} /> : null}

      <div className="token-grid">
        <div className="token-swatch">
          <span>{t("people.company")}</span>
          <strong>{company.name}</strong>
        </div>
        <div className="token-swatch">
          <span>{t("people.active_session")}</span>
          <strong>{currentUser.displayName || currentUser.loginId}</strong>
        </div>
        <div className="token-swatch">
          <span>{t("people.platform_role")}</span>
          <strong>{activeRole ? t(`people.role.${activeRole}`, { defaultValue: activeRole }) : t("people.signed_out")}</strong>
        </div>
      </div>

      {!loading ? (
        <>
          <div className="notification-list">
            {activeMembers.map((member) => (
              <div key={member.user_id ?? member.user} className="notification-item">
                <strong>{member.display_name || member.login_id || member.user}</strong>
                <p><bdi>{member.login_id || t("people.login_id_unavailable")}</bdi></p>
                <small>{member.role ? t(`people.role.${member.role}`, { defaultValue: member.role }) : t("people.role_unset")}</small>
              </div>
            ))}
            {activeMembers.length === 0 ? (
              <EmptyState title={t("people.no_members")} body={t("people.no_members_body")} />
            ) : null}
          </div>

          {canManagePeople ? (
            <>
              <form className="form-stack" onSubmit={createMember}>
                <h3>{isOwner ? t("people.create_company_user") : t("people.create_employee")}</h3>
                <div className="form-grid">
                  <label>
                    <span>{t("people.login_id")}</span>
                    <input
                      required
                      value={memberDraft.login_id}
                      dir="ltr"
                      onChange={(event) => setMemberDraft((current) => ({ ...current, login_id: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>{t("people.display_name")}</span>
                    <input
                      value={memberDraft.display_name}
                      onChange={(event) => setMemberDraft((current) => ({ ...current, display_name: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>{t("people.password")}</span>
                    <input
                      required
                      type="password"
                      dir="ltr"
                      value={memberDraft.password}
                      onChange={(event) => setMemberDraft((current) => ({ ...current, password: event.target.value }))}
                    />
                  </label>
                  {isOwner ? (
                    <label>
                      <span>{t("people.platform_role")}</span>
                      <select
                        value={memberDraft.role}
                        onChange={(event) => setMemberDraft((current) => ({ ...current, role: event.target.value }))}
                      >
                        <option value="employee">{t("people.role.employee")}</option>
                        <option value="monitor">{t("people.role.monitor")}</option>
                        <option value="owner">{t("people.role.owner")}</option>
                      </select>
                    </label>
                  ) : (
                    <>
                      <p className="muted">{t("people.monitor_employee_notice")}</p>
                      <label>
                        <span>{t("people.branch")}</span>
                        <select
                          required
                          value={memberDraft.branch_id}
                          onChange={(event) => setMemberDraft((current) => ({ ...current, branch_id: event.target.value }))}
                        >
                          <option value="">{t("people.select_branch")}</option>
                          {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name} - {branch.code}</option>)}
                        </select>
                      </label>
                      <label>
                        <span>{t("people.job_role")}</span>
                        <select
                          required
                          value={memberDraft.job_role_id}
                          onChange={(event) => setMemberDraft((current) => ({ ...current, job_role_id: event.target.value }))}
                        >
                          <option value="">{t("people.select_job_role")}</option>
                          {jobRoles.map((role) => <option key={role.id} value={role.id}>{role.name} - {role.code}</option>)}
                        </select>
                      </label>
                    </>
                  )}
                </div>
                <button className="primary-button" type="submit" disabled={saving === "member"}>
                  {t("people.create_user")}
                </button>
              </form>

              {isOwner ? <>
              <form className="form-stack" onSubmit={createBranch}>
                <h3>{t("people.create_branch")}</h3>
                <div className="form-grid">
                  <label>
                    <span>{t("people.name")}</span>
                    <input
                      required
                      value={branchDraft.name}
                      onChange={(event) => setBranchDraft((current) => ({ ...current, name: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>{t("people.code")}</span>
                    <input
                      required
                      value={branchDraft.code}
                      className="bidi-ltr"
                      dir="ltr"
                      onChange={(event) => setBranchDraft((current) => ({ ...current, code: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>{t("people.timezone")}</span>
                    <input
                      required
                      value={branchDraft.timezone}
                      className="bidi-ltr"
                      dir="ltr"
                      onChange={(event) => setBranchDraft((current) => ({ ...current, timezone: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>{t("people.operational_cutoff")}</span>
                    <input
                      required
                      type="time"
                      className="bidi-ltr"
                      dir="ltr"
                      step="1"
                      value={branchDraft.operational_day_cutoff}
                      onChange={(event) =>
                        setBranchDraft((current) => ({ ...current, operational_day_cutoff: event.target.value }))
                      }
                    />
                  </label>
                </div>
                <button className="ghost-button" type="submit" disabled={saving === "branch"}>
                  {t("people.create_branch")}
                </button>
              </form>

              <form className="form-stack" onSubmit={createJobRole}>
                <h3>{t("people.create_job_role")}</h3>
                <div className="form-grid">
                  <label>
                    <span>{t("people.name")}</span>
                    <input
                      required
                      value={jobRoleDraft.name}
                      onChange={(event) => setJobRoleDraft((current) => ({ ...current, name: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>{t("people.code")}</span>
                    <input
                      required
                      value={jobRoleDraft.code}
                      className="bidi-ltr"
                      dir="ltr"
                      onChange={(event) => setJobRoleDraft((current) => ({ ...current, code: event.target.value }))}
                    />
                  </label>
                </div>
                <button className="ghost-button" type="submit" disabled={saving === "job-role"}>
                  {t("people.create_job_role")}
                </button>
              </form>
              </> : null}

              <form className="form-stack" onSubmit={assignBranch}>
                <h3>{t("people.assign_branch_access")}</h3>
                <div className="form-grid">
                  <label>
                    <span>{t("people.user")}</span>
                    <select
                      required
                      value={assignmentDraft.user_id}
                      onChange={(event) => setAssignmentDraft((current) => ({ ...current, user_id: event.target.value }))}
                    >
                      <option value="">{t("people.select_user")}</option>
                      {activeMembers.map((member) => (
                        <option key={member.user_id ?? member.user} value={member.user_id ?? member.user}>
                          {member.display_name || member.login_id || member.user}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>{t("people.branch")}</span>
                    <select
                      required
                      value={assignmentDraft.branch_id}
                      onChange={(event) => setAssignmentDraft((current) => ({ ...current, branch_id: event.target.value }))}
                    >
                      <option value="">{t("people.select_branch")}</option>
                      {branches.map((branch) => (
                        <option key={branch.id} value={branch.id}>
                          {branch.name} - {branch.code}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>{t("people.job_role")}</span>
                    <select
                      required
                      value={assignmentDraft.job_role_id}
                      onChange={(event) => setAssignmentDraft((current) => ({ ...current, job_role_id: event.target.value }))}
                    >
                      <option value="">{t("people.select_job_role")}</option>
                      {jobRoles.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.name} - {role.code}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <button className="primary-button" type="submit" disabled={saving === "assignment"}>
                  {t("people.assign_branch")}
                </button>
              </form>
            </>
          ) : (
            <p className="muted">{t("people.management_restricted")}</p>
          )}
        </>
      ) : null}
    </Panel>
  );
}
