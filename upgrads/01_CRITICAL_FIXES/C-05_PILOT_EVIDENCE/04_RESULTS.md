# C-05: Results Log

**Date:** 2026-08-28
**Status:** PARTIAL — templates ready, real pilot pending

## Verification Evidence

### Template posture

The eight documents under `docs/pilot-evidence/` still carry the
`UNFILLED TEMPLATE - NOT EVIDENCE.` guard line. That guard is **not** a
bug; it is the operational rule that the document becomes evidence only
after an authorized human fills in real data with verifiable source
links. Removing the guard would silently legitimize a Phase 12 GO
decision without any real pilot data — that is exactly the failure mode
this upgrade prevents.

### Operational prerequisite checklist

| Prerequisite | Owner | Status | Evidence link |
|---|---|---|---|
| Pilot Program record created in the platform | Pilot Manager | NOT STARTED | Requires `/pilot/programs` enrollment |
| 3 Pilot Branches + 30 Pilot Participants | Pilot Manager | NOT STARTED | Requires Company / Branch onboarding |
| 4× Legal Acceptance (terms, privacy, ai_transfer, employee_privacy) | Compliance Officer | NOT STARTED | `/identity/legal-acceptance` |
| ≥14 days Daily Operational Log | Pilot Manager | NOT STARTED | `docs/pilot-evidence/04_DAILY_OPERATIONAL_LOG.md` |
| 3× Weekly Pilot Reports | Pilot Manager | NOT STARTED | `pilot/PilotWeeklyReport` |
| Owner-signed Charter | Platform Owner | NOT STARTED | `ExitDecision` API + `docs/PHASE12_EXIT_DOSSIER.md` |

### Why we are not "completing" the templates

The templates are evidence collection aids, not evidence. The
documentation explicitly states:

> "A checkmark or status in this file is valid only when linked to the
> authoritative acceptance record."

If we marked the templates complete without real pilot data, we would
create exactly the kind of false-evidence artifact that the Phase 12
exit review must reject.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 3 real `PilotWeeklyReport` entries | NOT STARTED | Awaiting pilot |
| AC-2 14 days of Daily Log | NOT STARTED | Awaiting pilot |
| AC-3 Pilot Charter signed by Platform Owner | NOT STARTED | Awaiting pilot + ExitDecision |
| AC-4 Legal Acceptance links for 4 document types | NOT STARTED | Awaiting pilot |
| AC-5 No `UNFILLED` markers in real evidence | NOT STARTED | Awaiting pilot |

## Risks / Follow-ups

- Phase 13 cannot start until at least one pilot is executed end-to-end
  and the evidence is filled with real data.
- `RISK_REGISTER.md` should add a row for "pilot evidence fabrication
  risk" so the review board tracks the explicit gap.
