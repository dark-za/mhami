# Phase 12 Branch, Role, Shift, and Chrome Device Roster

> **UNFILLED TEMPLATE - NOT EVIDENCE.** Populate only with authorized pilot operational records. Do not use this template to invent participant, device, or assignment data.

## Record Control

| Field | Value |
| --- | --- |
| Roster ID | `P12-ROSTER-<pilot-program-id>-<YYYYMMDD>` |
| PilotProgram ID | `<uuid>` |
| Company ID / code | `<uuid> / <code>` |
| Effective from / through | `<ISO-8601> / <ISO-8601 or ongoing>` |
| Prepared by (account ID) | `<account-id>` |
| Reconciled by (account ID) | `<account-id>` |
| Reconciliation evidence link | `<system export or approved record>` |

## Branch Register

| Branch ID | Branch code | Name | Timezone | Operational-day cutoff | Active | Branch owner/monitor account ID | Evidence link |
| --- | --- | --- | --- | --- | --- | --- |
| `<uuid>` | `<code>` | `<name>` | `<IANA timezone>` | `<HH:MM>` | `yes/no` | `<account-id>` | `<link>` |

## Participant and Shift Register

Use account IDs, not unnecessary personal details. Add one row for every active owner, Quality Monitor, and employee.

| Participant row ID | Account ID | Company role | Branch ID | Job role code | Membership type | Shift ID / weekday | Start-end local | Active from / until | Legal status (`03`) | Evidence link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-PART-<account-id>` | `<account-id>` | `owner / monitor / employee` | `<uuid>` | `<code>` | `primary / transfer` | `<id / Mon-Sun>` | `<HH:MM-HH:MM>` | `<dates>` | `complete / incomplete / not-applicable` | `<link>` |

## Chrome Device Register

Record only managed, enrolled ChromeOS/Chrome devices approved for pilot capture. A device without an accountable branch and operational contact is not eligible for pilot task capture.

| Device row ID | Device asset ID | Branch ID | Station/use | Chrome/ChromeOS version | Managed/enrolled | Assigned shift/role | Checked date/time (UTC) | Checked by (account ID) | Evidence link | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-DEV-<asset-id>` | `<asset-id>` | `<uuid>` | `<station>` | `<version>` | `yes/no` | `<shift or role>` | `<ISO-8601>` | `<account-id>` | `<link>` | `approved / blocked / retired` |

## Reconciliation Exceptions

| Exception ID | Record type | Identifier | Gap | Interim control | Accountable owner | Due date | Issue link | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-ROSTER-EX-001` | `participant / shift / device / branch` | `<id>` | `<description>` | `<control>` | `<account-id>` | `<YYYY-MM-DD>` | `<07 register link>` | `open / resolved` |

## Acceptance Criteria and STOP Markers

- [ ] Three to five active branches are recorded with timezone and operational-day cutoff.
- [ ] Every active participant has exactly one current company role and an authorized branch/job-role assignment, except documented transfers.
- [ ] Every planned task-capture station has an enrolled Chrome device and completion check.
- [ ] Every participant marked active for task activity is `complete` in the legal reconciliation.

**STOP `P12-STOP-04`:** Do not schedule or permit task activity for a participant without complete required legal acceptance, an active role/branch assignment, or approved Chrome capture access. Record the exception in `07_ISSUE_CHANGE_DISPOSITION_REGISTER.md`.
