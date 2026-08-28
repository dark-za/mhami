# Phase 12 Pilot Charter and Owner Authorization

> **UNFILLED TEMPLATE - NOT EVIDENCE.** This document becomes evidence only when the required system records and authorization evidence links are completed by authorized humans. It does not record a Phase 12 GO decision.

## Record Control

| Field | Value |
| --- | --- |
| Charter ID | `P12-CHARTER-<pilot-program-id>` |
| Version | `<version>` |
| Status | `draft / active / suspended / closed` |
| Prepared by (account ID) | `<account-id>` |
| Prepared date (UTC) | `<YYYY-MM-DD>` |
| Last reviewed date (UTC) | `<YYYY-MM-DD>` |
| Canonical record link | `<PilotProgram/API or approved record link>` |

## Authorization and Scope

| Field | Value |
| --- | --- |
| Company ID / code | `<company-uuid> / <company-code>` |
| PilotProgram ID | `<uuid>` |
| Pilot owner account ID | `<account-id>` |
| Owner authorization status | `pending / authorized / withdrawn` |
| Authorization date/time (UTC) | `<ISO-8601>` |
| Authorization evidence link | `<signed approval or auditable system record>` |
| Observation start / end (local + timezone) | `<start> / <end>` |
| Test environment | `<staging-equivalent pilot environment>` |
| Branch target | `<3-5>` |
| Employee target | `<approximately 30>` |
| Chrome device target | `<count>` |
| Connector owner account/team | `<identifier>` |
| AI provider / mode | `<provider> / Shadow Mode only>` |

## Operating Commitments

| ID | Commitment | Accountable owner | Evidence link | Acceptance criterion | Status |
| --- | --- | --- | --- | --- | --- |
| `P12-CH-01` | Participants, branches, shifts, roles, and Chrome devices are reconciled before task activity. | `<account-id>` | `<02 roster link>` | Every active participant and device assignment is represented or explicitly excepted. | `open` |
| `P12-CH-02` | Required legal acceptance is reconciled before a participant performs task activity. | `<account-id>` | `<03 reconciliation link>` | Four required acceptance records are linked for every active participant. | `open` |
| `P12-CH-03` | Approved starter task templates are operated through Chrome-only capture without gallery-upload fallback. | `<account-id>` | `<daily log links>` | Actual activity and blocked fallback attempts, if any, are logged. | `open` |
| `P12-CH-04` | Owners, monitors, and employees operate routine workflows without engineering intervention. | `<account-id>` | `<04 and 05 links>` | Routine workflow result and exceptions are logged for the observation period. | `open` |
| `P12-CH-05` | AI remains in Shadow Mode; no AI auto-pass is enabled. | `<account-id>` | `<05 and 06 links>` | All observed runs show Shadow Mode and no auto-pass activation. | `open` |

## STOP Markers

| STOP ID | Trigger | Immediate action | Notify | Resolution evidence link | Cleared by / date |
| --- | --- | --- | --- | --- | --- |
| `P12-STOP-01` | Tenant isolation, media protection, audit integrity, or recovery failure. | Stop affected pilot activity; preserve records; follow incident response. | `<pilot owner / on-call>` | `<incident/evidence link>` | `<account-id / date>` |
| `P12-STOP-02` | AI auto-pass is enabled or activated without the approved evidence gate. | Stop AI-dependent pilot activity; retain audit evidence. | `<pilot owner / connector owner>` | `<evidence link>` | `<account-id / date>` |
| `P12-STOP-03` | Routine pilot operation requires engineering intervention. | Pause affected workflow; create issue and assess scope. | `<pilot owner>` | `<issue link>` | `<account-id / date>` |
| `P12-STOP-04` | Required legal acceptance is missing for an active participant. | Do not permit that participant's task activity; record issue. | `<pilot owner / monitor>` | `<03 reconciliation and issue link>` | `<account-id / date>` |

## Owner Authorization Attestation

Complete only after the owner has reviewed this charter and the linked operating commitments. This attestation authorizes the internal pilot scope only; it is **not** a Phase 12 exit GO decision and does not replace legal counsel review or legal acceptance records.

| Field | Value |
| --- | --- |
| Owner account ID | `<account-id>` |
| Owner role | `Platform Owner / internal operations lead` |
| Authorization decision | `authorize / decline / withdraw` |
| Decision date/time (UTC) | `<ISO-8601>` |
| Signature or approved electronic-record reference | `<reference>` |
| Conditions or exclusions | `<text or none>` |

## Completion Check

- [ ] PilotProgram and company identifiers are linked.
- [ ] Observation period, accountable owners, and success measures are recorded.
- [ ] Owner authorization is linked to an authentic human approval record.
- [ ] All active STOP markers are resolved or the pilot is paused.
- [ ] This charter is linked from the Phase 1 handoff checklist.
