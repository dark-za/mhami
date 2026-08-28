# Phase 12 Pilot Completion Report

## Status

Issued by `PILOT-ASSURANCE-02` for the Phase 12 Internal Pilot exit dossier.

## Objective

Validate the complete V1 flow with an internal company across three branches and approximately thirty employees before external self-service SaaS use.

## Pilot Configuration Evidence

The seeded pilot (`docs/PILOT_PROFILE.md`, `seed_pilot` management command) provisions:

- One internal operating company (food-service / quick-service-restaurant sector) modeled as a single `Company` with a one-to-one `PilotProgram`.
- Three branches, each a distinct tenant (`Branch.company_id`), each with an operational-day cutoff.
- Owner, two Quality Monitors, and ten employees per branch (30 total) with `CompanyMembership` roles (`OWNER`, `MONITOR`, `EMPLOYEE`) and branch-scoped `UserBranchMembership`.
- Two Chrome devices per branch (`chrome_device_count`), enforcing the Chrome-only browser policy with no gallery-upload fallback.
- Weekly shift patterns per employee.
- Approved starter templates from `docs/PILOT_TASK_CATALOG.md`.

Program fields used as the exit baseline (`PilotProgram`):

- `branch_count_target=3`
- `employee_count_target=30`
- `test_environment=staging-equivalent`
- `ai_provider_name` (private vision model, Shadow Mode only)
- `connector_owner` (internal SRE / connector team)
- `success_measures`, `escalation_contacts`, `operating_checklist`, `weekly_metrics_goal`

## Success Measures and Measurable Results

The approved success measures (baseline in `pilot_program_for_company` and `seed_pilot`):

1. **Employees complete Chrome-only tasks.**
2. **Monitors resolve exceptions without engineering intervention.**
3. **Owners see weekly branch and quality trends.**

Each measure is supported by an implemented, test-covered capability in this codebase:

| # | Success measure | Supporting evidence | Result basis |
| --- | --- | --- | --- |
| 1 | Chrome-only task completion | `EvidenceItem` capture via `CaptureSession`; browser-only policy; face-blur derivatives (`blurred_media_name`); no gallery fallback | Automated + seeded flow; requires real pilot volume for final figures |
| 2 | Monitor exception handling without engineering | `ReviewDecision` workflow, issue creation/resolution via `PilotIssue`; branch-scoped review queue | `reviews/tests/test_reviews_api.py`; `pilot/tests/test_api.py` |
| 3 | Owner weekly branch/quality trends | `pilot_dashboard`, `PilotWeeklyReport`, review dashboard | `pilot/tests/test_api.py`; `reviews/tests/test_reviews_api.py` |

## Measurable Pilot Results

The tables below record the **observed operational ranges** the pilot is designed to measure. Final acceptance requires the values populated from the actual pilot observation period (at least one `PilotWeeklyReport`). Placeholder confidence is explicitly **not** claimed as a pass.

| Metric | Pilot target (from `PILOT_PROFILE.md`) | Evidence source | Current status |
| --- | --- | --- | --- |
| Task instances | ~30–60 per branch per day | `TaskInstance` scheduling (`schedule_due_tasks`) | Measurable via weekly report |
| Evidence images | ~150–400 per branch per day at peak | `EvidenceItem.evidence_type=image` | Measurable via weekly report |
| Camera failures | Recorded as `PilotIssue` / operational log | Issue backlog | Tracked |
| Upload failures | Recorded as `PilotIssue` / `CaptureSession` status | Issue backlog | Tracked |
| Face-blur behavior | `EvidenceItem.face_detected` and `blurred_media_name` | Evidence model | Measurable via weekly report |
| AI agreement rate | `PilotWeeklyReport.ai_agreement_rate` computed from `AIAnalysisRun.agreement_with_human` | `pilot/services.py:_ai_agreement_rate` | Computable; needs real runs |
| Review workload | `ReviewDecision` counts per week | Dashboard summary `reviews_created` | Measurable |
| Duplicate-risk signals | `EvidenceItem.duplicate_risk_score` | Evidence model | Measurable |
| Connector health | `TenantConnectorEnrollment.health_status` | Connector model + API | Measurable |

## Resilience and Authorization Verification (Scope 2)

The following paths are exercised and covered by automated tests. None halted evidence submission and none caused automatic acceptance:

- **Tenant and branch isolation.** `Company`/`Branch` scope enforced; branch-scoped review queue (`test_review_queue_is_branch_scoped`), monitor cannot decide unassigned branch (`test_monitor_cannot_decision_unassigned_branch`), employee cannot resolve pilot issue (`test_employee_cannot_resolve_issue`).
- **Support authorization boundaries.** Branch-scoped export authorization (`test_monitor_cannot_export_unassigned_branch`), owner/monitor-only pilot mutation (`_owner_or_monitor`).
- **Connector outage does not halt evidence submission.** Connector health is observable and revocable (`test_connector_revoke_sets_offline_status`); evidence submission does not depend on connector status.
- **AI failure does not halt submission or create automatic acceptance.** `AIAnalysisStatus.FAILED` is an allowed state; AI remains in Shadow Mode (`auto_pass_enabled=False`, `shadow_mode=True`); no auto-pass path is enabled during the pilot.
- **Export and 90-day read-only tenant path.** Authorized export request/download and branch scoping (`test_exports_api.py`); tenant read-only path exercised with safe fixtures.
- **Backup and restore evidence remains current.** Backup create/download/restore with DB verification (`test_backup_create_download_restore`), backed by `docs/PHASE11_RESTORE_TEST_REPORT.md`.

## Verification Checklist Results

| Verification item | Result |
| --- | --- |
| Employees complete required tasks from Chrome without gallery-upload fallback | Capability present; final pass requires real pilot volume |
| Owner, monitor, employee roles exercised against realistic tenant/branch data | Verified via seeded roles + branch-scoped tests |
| Issues created/resolved without engineering intervention | Verified (`PilotIssue` workflow + test) |
| Change requests created/approved/rejected through the application | Verified (`PilotChangeRequest` workflow + test) |
| Pilot dashboard and weekly reports contain actual data rather than seed-only values | Requires completed `PilotWeeklyReport`; structure verified |
| Connector and AI Shadow Mode observed | Verified (`connector_control`, `ai_gateway` tests) |

## Conclusion

The platform implements and protects every Phase 12 verification requirement. **The pilot completion report cannot be signed as final until the actual pilot observation period populates at least one weekly metrics report with real task, image, failure, blur, review, duplicate, AI-agreement, connector, and usability values.** All capability-level evidence is present; the go/no-go decision in the exit dossier records this as **conditionally met, pending owner sign-off on real pilot data or an approved release decision**.
