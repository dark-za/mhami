# Phase 12: Internal Pilot

## Status

Exit dossier issued by `PILOT-ASSURANCE-02`. Staging-equivalent pilot evidence is complete; the remaining blocker is the owner-recorded Phase 12 exit decision. See `docs/PHASE12_EXIT_DOSSIER.md` and the companion Phase 12 reports in `docs/`.

## Objective

Validate the complete V1 flow with an internal company across three to five branches and approximately thirty employees before exposing self-service SaaS use to external customers.

## Entry Requirements

- Phase 11 is complete.
- Pilot company, branches, owner, monitors, employees, Chrome devices, shifts, and task templates are configured.
- Terms, privacy notice, employee acknowledgement, and AI transfer acceptance are in place.
- Backup restore, security tests, and staging release candidate pass.

## Scope

- Run the approved starter templates and any company-approved generic templates.
- Operate self-registration, trial lifecycle, branding, bilingual interface, Chrome-only browser policy, exports, MFA, connector, and AI Shadow Mode as part of the actual pilot.
- Measure actual image volume, camera failures, face-blur behavior, upload failures, task completion, review workload, duplicate-risk signals, AI agreement, connector reliability, and user confusion.
- Validate company and branch isolation through realistic users and support authorization.
- Capture documented feedback without bypassing audit, safety, or deployment practices.

## Required Software and Services

- Staging-equivalent pilot deployment.
- Tenant Connector on Linux Docker if the pilot uses a private provider.
- Monitoring, backups, system status, and support process.
- Pilot issue tracking and change-control process.

## Security and Data Requirements

- Pilot evidence is treated as production-like personal and operational data.
- No production shortcut bypasses MFA, tenant scope, private media authorization, face handling, or audit.
- AI remains in Shadow Mode until risk-level evidence thresholds and owner review are met.
- Any performance restriction is based on final human outcomes and remains monitor-overridable.

## Deliverables

- Pilot configuration record and signed operating checklist.
- Weekly pilot metrics report.
- AI agreement and error analysis.
- Capacity findings, including observed evidence volume and storage growth.
- Prioritized defect and usability backlog.
- Updated risk register and approved change requests.

## Verification

- Employees complete tasks from Chrome without gallery upload fallback.
- Monitors process alerts, issues, retries, missed decisions, and corrections.
- Owners review branch completion, quality exceptions, performance policies, and trial status.
- Connector outage and AI failure do not halt evidence submission.
- Export and 90-day read-only tenant path are tested using safe fixtures.

## Exit Criteria

- Pilot success measures show improved operational visibility, useful exception handling, acceptable employee usability, and understood AI behavior.
- High-severity defects are resolved or have approved release decisions.
- Capacity, recovery, legal-policy, and support findings are incorporated into the release candidate.

## Stop Conditions

- Tenant isolation, media protection, audit integrity, or recovery failures are found.
- AI auto-pass is enabled without the approved risk-level evidence gate.
- The pilot cannot be operated without engineering intervention for routine workflows.
