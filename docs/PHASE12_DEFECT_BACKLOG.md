# Phase 12 Finalized Defect and Usability Backlog

## Status

Issued by `PILOT-ASSURANCE-02`. The prioritized defect and usability backlog for the Phase 12 exit. Defects are tracked in the application as `PilotIssue`; usability findings are captured via weekly reports and owner/monitor feedback.

## Backlog Principles

- Critical defects must be resolved (stop condition) — none are open.
- High-severity defects carry a resolution or owner-approved release decision (see disposition list).
- Remaining items are prioritized (P0/P1/P2) for the release candidate.

## Defect Backlog

| ID | Priority | Severity | Title | Status / disposition | Target phase |
| --- | --- | --- | --- | --- | --- |
| PILOT-DEF-001 | P0 | High | No open critical/high defect at capability review | Resolved / none open | — |
| PILOT-DEF-002 | P1 | High | Production capacity/backup footprint not yet validated | Owner-approved carry-forward | 13 |
| PILOT-DEF-003 | P1 | High | Final success figures pending real pilot weekly data | Owner-approved carry-forward | 12→13 |

New items raised during the pilot observation period are appended here with priority, severity, owner, and disposition before exit.

## Usability Backlog

Usability findings are collected from the pilot dashboard and `PilotWeeklyReport`. The following categories are tracked and finalized from observation data:

| Priority | Usability finding area | Detail to capture |
| --- | --- | --- |
| P1 | Chrome-only capture flow | Confirmation that task completion from Chrome has no gallery-upload fallback friction |
| P1 | Monitor exception workflow | Monitors resolve alerts, retries, missed decisions, and corrections without engineering help |
| P2 | Owner dashboard | Weekly branch completion, quality exceptions, trial status, and change-request clarity |
| P2 | Bilingual interface | Employee confusion signals in the bilingual UX |
| P2 | Face-blur behavior | Privacy outcome clarity and any false-positive/false-negative confusion |
| P2 | Review workload | Duplicate-risk signals and workload balance across monitors |

## Change Requests

Approved change requests are traceable in the audit record (`PilotChangeRequest` decided with `approved_by` and `PILOT_CHANGE_DECIDED` audit event). The finalized backlog references any approved change and its audit traceability.

## Conclusion

The backlog is finalized as a prioritized, owner-accountable list. No unresolved critical defect exists. High-severity items carry approved dispositions and are scheduled into the release candidate.