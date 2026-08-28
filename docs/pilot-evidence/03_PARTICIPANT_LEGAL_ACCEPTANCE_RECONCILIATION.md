# Phase 12 Per-Participant Legal Acceptance Reconciliation

> **UNFILLED TEMPLATE - NOT EVIDENCE.** This is an operational reconciliation aid, not legal text, legal advice, legal acceptance, or a substitute for qualified legal counsel review. A checkmark or status in this file is valid only when linked to the authoritative acceptance record.

## Record Control

| Field | Value |
| --- | --- |
| Reconciliation ID | `P12-LEGAL-<pilot-program-id>-<YYYYMMDD>` |
| PilotProgram ID | `<uuid>` |
| Company ID / code | `<uuid> / <code>` |
| Document policy version set | `<terms-version>; <privacy-version>; <employee-privacy-version>; <ai-transfer-version>` |
| Reconciled at (UTC) | `<ISO-8601>` |
| Reconciled by (account ID) | `<account-id>` |
| Authoritative source link | `<acceptance export/API/audit link>` |

## Required Document Keys

| Key | Required document | Authoritative document path | Required before task activity |
| --- | --- | --- | --- |
| `terms` | Terms of Use | [`../legal/TERMS_OF_USE.md`](../legal/TERMS_OF_USE.md) | `yes` |
| `privacy` | Privacy Notice | [`../legal/PRIVACY_NOTICE.md`](../legal/PRIVACY_NOTICE.md) | `yes` |
| `employee_privacy` | Employee Privacy Acknowledgement | [`../legal/EMPLOYEE_PRIVACY_ACKNOWLEDGEMENT.md`](../legal/EMPLOYEE_PRIVACY_ACKNOWLEDGEMENT.md) | `yes` |
| `ai_transfer` | AI Data Transfer Notice | [`../legal/AI_DATA_TRANSFER_NOTICE.md`](../legal/AI_DATA_TRANSFER_NOTICE.md) | `yes` |

## Participant Reconciliation Register

Add one row for each active owner, monitor, and employee. Record the actual `LegalAcceptance` identifier, document version, acceptance timestamp, and source link for all four document types. Do not enter a signature, date, or acceptance ID unless it exists in the authoritative record.

| Participant row ID | Account ID | Role | Branch ID | `terms` ID/version/time/link | `privacy` ID/version/time/link | `employee_privacy` ID/version/time/link | `ai_transfer` ID/version/time/link | Complete | Reconciled by / date | Exception ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-LEGAL-PART-<account-id>` | `<account-id>` | `<owner/monitor/employee>` | `<uuid or n/a>` | `<id / version / UTC / link>` | `<id / version / UTC / link>` | `<id / version / UTC / link>` | `<id / version / UTC / link>` | `yes/no` | `<account-id / UTC>` | `<P12-LEGAL-EX-### or none>` |

## Exceptions and Resolution

| Exception ID | Participant row ID | Missing/invalid item | Detected date/time (UTC) | Task activity blocked | Accountable owner | Correction evidence link | Cleared by / date | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-LEGAL-EX-001` | `<row-id>` | `<document/version/source gap>` | `<ISO-8601>` | `yes` | `<account-id>` | `<authoritative record link>` | `<account-id / UTC>` | `open / resolved` |

## Reconciliation Acceptance Criteria

- [ ] Every active participant has one linked, authoritative acceptance record for all four required document keys.
- [ ] Each linked record identifies its document version and acceptance timestamp.
- [ ] Any missing, revoked, mismatched, or unverifiable acceptance is recorded as an open exception and the participant is blocked from task activity.
- [ ] The reconciliation timestamp is no earlier than the first task activity for each participant, or an exception explains the discrepancy.

**STOP `P12-STOP-04`:** Missing or unverifiable required acceptance means no task activity for that participant. Escalate to the pilot owner and record the issue/change-register ID. Legal documents in `docs/legal/` are placeholders pending qualified legal review; their presence alone is not evidence of legally valid acceptance.
