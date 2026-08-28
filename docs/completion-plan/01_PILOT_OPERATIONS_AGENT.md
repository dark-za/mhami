# Phase 1: Internal Pilot Operations

## Assigned Agent

`PILOT-OPS-01`

## Objective

Run the Phase 12 internal pilot with a real internal company and collect reliable operational evidence. This phase starts from the current project position: Phases 00 through 11 are complete, Phase 12 is in progress, and Phase 13 must not begin yet.

## Required Inputs

- Approved Phase 12 gate document: `docs/phases/12_INTERNAL_PILOT.md`.
- Pilot profile and task catalog: `docs/PILOT_PROFILE.md` and `docs/PILOT_TASK_CATALOG.md`.
- Pilot operations procedure: `docs/runbooks/PILOT_OPERATIONS.md`.
- Fillable operational handoff package: `docs/pilot-evidence/08_PHASE1_HANDOFF_CHECKLIST.md` (unfilled templates; not evidence until completed and linked).
- Staging-equivalent stack, working backups, system status, support process, and the seeded pilot environment.
- Real pilot owner, monitors, employees, branches, Chrome devices, and approved task templates.

## Scope

1. Configure the real internal pilot company for three to five branches and approximately thirty employees.
2. Confirm owner, monitor, employee, branch, shift, role, and Chrome-device assignments.
3. Confirm terms, privacy notice, employee acknowledgement, and AI transfer acceptance before task activity.
4. Run the approved starter task templates through Chrome-only evidence capture.
5. Operate the daily pilot loop:
   - Employees submit assigned tasks and evidence.
   - Monitors process alerts, retries, missed decisions, issues, and corrections.
   - Owners review pilot dashboard, branch completion, quality exceptions, trial status, and change requests.
6. Create and maintain pilot issues, change requests, and weekly pilot reports through the supported application workflow.
7. Capture raw operational observations: task volume, image volume, camera failures, upload failures, face-blur behavior, review workload, duplicate-risk signals, AI agreement, connector health, and usability feedback.

## Explicit Exclusions

- Do not enable AI auto-pass.
- Do not enable external self-service SaaS onboarding.
- Do not bypass MFA, tenant scope, private-media authorization, face handling, audit logging, or change control.
- Do not begin Phase 13 production launch activities.

## Required Deliverables

- Completed pilot configuration record and signed operating checklist.
- Evidence that every pilot participant has the required legal acknowledgements.
- Branch/employee/Chrome-device assignment record.
- Daily operational log for alerts, incidents, retries, corrections, and support requests.
- At least one weekly pilot metrics report populated with actual observations.
- Pilot issue backlog and change-request register with accountable owners.

## Verification Checklist

- Employees complete required tasks from Chrome without gallery-upload fallback.
- Owner, monitor, and employee roles are exercised against realistic tenant and branch data.
- Issues can be created and resolved without engineering intervention.
- Change requests can be created and approved or rejected through the application.
- The pilot dashboard and weekly reports contain actual data rather than seed-only values.
- Connector and AI Shadow Mode behavior are observed in the pilot environment.

## Exit Gate

The agent may hand off to `PILOT-ASSURANCE-02` only when:

- The pilot has run for an agreed observation period with real users and data.
- All required operational records and at least one weekly report exist.
- No active stop condition from Phase 12 is present.
- Outstanding high-severity issues are explicitly assigned and tracked.

## Stop Conditions

- Tenant isolation, media protection, audit integrity, or recovery failure.
- AI auto-pass becomes enabled without the approved evidence gate.
- Routine pilot operation requires engineering intervention.
