# Phase 12 Issue and Change Disposition Register

> **UNFILLED TEMPLATE - NOT EVIDENCE.** Record observed issues and requested changes only. This template does not approve a change, waive a defect, or create an owner release decision unless linked to an authentic, authorized decision record.

## Record Control

| Field | Value |
| --- | --- |
| Register ID | `P12-DISP-<pilot-program-id>-<YYYYMMDD>` |
| PilotProgram ID | `<uuid>` |
| Maintainer account ID | `<account-id>` |
| Last reconciled (UTC) | `<ISO-8601>` |
| In-app issues/changes source link | `<link>` |

## Issue Register

| Issue ID | In-app PilotIssue ID | Opened (UTC) | Title / factual impact | Severity | Affected branch/workflow | STOP marker | Containment | Accountable owner | Evidence links | Status | Resolution or owner-approved release-decision link | Closed/reviewed (UTC) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-ISS-001` | `<uuid>` | `<ISO-8601>` | `<description>` | `low / medium / high / critical` | `<scope>` | `<id or none>` | `<action>` | `<account-id>` | `<links>` | `open / mitigated / resolved / carried` | `<link>` | `<ISO-8601>` |

## Change Request Register

| Change ID | In-app PilotChangeRequest ID | Requested (UTC) | Title / rationale | Risk and affected workflow | Requested by | Decision | Decided by / date | Decision evidence link | Implementation/validation evidence link | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-CHG-001` | `<uuid>` | `<ISO-8601>` | `<description>` | `<risk>` | `<account-id>` | `requested / approved / rejected / withdrawn` | `<account-id / UTC>` | `<link>` | `<link>` | `<status>` |

## Disposition Review

| Review ID | Review date (UTC) | Reviewer account ID | Open critical/high issue IDs | Decision needed | Owner decision evidence link | Next action / due date |
| --- | --- | --- | --- | --- | --- | --- |
| `P12-DISP-REV-001` | `<ISO-8601>` | `<account-id>` | `<IDs or none>` | `<resolve / release decision / continue pilot>` | `<link>` | `<action / date>` |

## Acceptance Criteria and STOP Markers

- [ ] Every issue has an accountable owner, severity, source evidence, status, and follow-up date.
- [ ] Every change request has an in-app identifier or a documented reason it could not be recorded through the supported workflow.
- [ ] High-severity issues are resolved or have an explicit, linked owner-approved release decision before Phase 12 exit consideration.
- [ ] Critical tenant-isolation, media-protection, audit-integrity, recovery, or security issues remain STOP conditions until resolved and independently reviewed.
- [ ] An AI auto-pass request is rejected or blocked unless the separately approved evidence gate exists; no template entry authorizes auto-pass.

**STOP:** Do not close or carry a critical issue without linked evidence of resolution and the required review. A high-severity issue cannot be treated as acceptable without an authentic owner-approved release decision; this register does not create that decision.
