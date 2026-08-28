# Phase 1 Pilot Operations Handoff Checklist

> **UNFILLED TEMPLATE - NOT EVIDENCE.** This checklist supports a handoff from `PILOT-OPS-01` to `PILOT-ASSURANCE-02`. Completion of this template does not authorize Phase 13, alter Phase 12 status, or create a platform-owner GO decision.

## Handoff Control

| Field | Value |
| --- | --- |
| Handoff ID | `P12-HANDOFF-<pilot-program-id>-<YYYYMMDD>` |
| PilotProgram ID | `<uuid>` |
| Company ID / code | `<uuid> / <code>` |
| Observation period | `<start-end and timezone>` |
| Prepared by (PILOT-OPS-01 account ID) | `<account-id>` |
| Received by (PILOT-ASSURANCE-02 account ID) | `<account-id>` |
| Prepared / received (UTC) | `<ISO-8601> / <ISO-8601>` |
| Handoff status | `draft / submitted / accepted / returned` |

## Required Package Index

| Package ID | Required artifact | Path or authoritative record link | Owner | Date current | Acceptance criterion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `P12-PKG-01` | Pilot charter and owner authorization | [`01_PILOT_CHARTER_AND_OWNER_AUTHORIZATION.md`](01_PILOT_CHARTER_AND_OWNER_AUTHORIZATION.md) | `<account-id>` | `<date>` | Scope, owner authorization, and active STOP markers are linked. | `pending` |
| `P12-PKG-02` | Branch/role/shift/Chrome device roster | [`02_BRANCH_ROLE_SHIFT_CHROME_DEVICE_ROSTER.md`](02_BRANCH_ROLE_SHIFT_CHROME_DEVICE_ROSTER.md) | `<account-id>` | `<date>` | Active assignments and exceptions are reconciled. | `pending` |
| `P12-PKG-03` | Per-participant legal acceptance reconciliation | [`03_PARTICIPANT_LEGAL_ACCEPTANCE_RECONCILIATION.md`](03_PARTICIPANT_LEGAL_ACCEPTANCE_RECONCILIATION.md) | `<account-id>` | `<date>` | All active participants have linked required acceptance records or are blocked. | `pending` |
| `P12-PKG-04` | Daily operational logs | [`04_DAILY_OPERATIONAL_LOG.md`](04_DAILY_OPERATIONAL_LOG.md) | `<account-id>` | `<date>` | Observation-period logs have source evidence and STOP handling. | `pending` |
| `P12-PKG-05` | Weekly metrics workbook | [`05_WEEKLY_METRICS_WORKBOOK.md`](05_WEEKLY_METRICS_WORKBOOK.md) | `<account-id>` | `<date>` | At least one actual-data week covers capacity, capture, review, duplicate, AI, connector, and usability metrics. | `pending` |
| `P12-PKG-06` | Resilience-test evidence index | [`06_RESILIENCE_TEST_EVIDENCE_INDEX.md`](06_RESILIENCE_TEST_EVIDENCE_INDEX.md) | `<account-id>` | `<date>` | Required paths have indexed actual exercise evidence or explicit blockers. | `pending` |
| `P12-PKG-07` | Issue/change disposition register | [`07_ISSUE_CHANGE_DISPOSITION_REGISTER.md`](07_ISSUE_CHANGE_DISPOSITION_REGISTER.md) | `<account-id>` | `<date>` | All issues/changes are traceable; high severity is resolved or has linked owner decision. | `pending` |

## Phase 1 Exit-Gate Check

| Check ID | Requirement | Evidence link | Result | Reviewer / date |
| --- | --- | --- | --- | --- |
| `P12-HO-01` | Agreed observation period with real users and real pilot data is complete. | `<links>` | `pass / fail / blocked` | `<account-id / UTC>` |
| `P12-HO-02` | Required operational records and at least one weekly actual-data report exist. | `<links>` | `pass / fail / blocked` | `<account-id / UTC>` |
| `P12-HO-03` | No active Phase 12 STOP condition is present. | `<01/04/06/07 links>` | `pass / fail / blocked` | `<account-id / UTC>` |
| `P12-HO-04` | Outstanding high-severity issues are explicitly assigned and tracked. | `<07 link>` | `pass / fail / blocked` | `<account-id / UTC>` |

## Handoff Decision

| Field | Value |
| --- | --- |
| PILOT-OPS-01 submission statement | `<factual statement with package links>` |
| PILOT-ASSURANCE-02 receipt decision | `accept for assurance review / return for completion` |
| Receipt evidence link | `<auditable record>` |
| Open blockers and accountable owners | `<IDs / owners / dates>` |
| Phase 12 exit decision | `NOT RECORDED HERE` |
| Phase 13 authorization | `NOT AUTHORIZED HERE` |

**STOP:** Do not submit as complete if legal reconciliation is incomplete for active participants, real-user observation evidence is absent, a required resilience exercise lacks disposition, or any Phase 12 STOP condition remains active. The platform owner alone records any Phase 12 GO/NO-GO decision in the designated exit-decision process.
