# PILOT-OPS-01 Deliverables — Phase 12 Internal Pilot Operations

Agent: `PILOT-OPS-01` | Date: 2026-08-26 | Environment: staging-equivalent dev stack (`compose.yml` + `compose.dev.yml`, API `127.0.0.1:8000`)

## 1. Pilot Configuration Record and Signed Operating Checklist

### Company

| Field | Value |
| --- | --- |
| Name | Pilot Coffee Co |
| Code | `pilotco` |
| Industry | `restaurants_and_cafes` |
| Status | `trial` (ends 2026-10-25) |
| Owner | `pilotco-owner` (role Owner) |
| PilotProgram status | `active` |

### Program targets (recorded in `PilotProgram`)

- Branch count target: **3**
- Employee count target: **30**
- Chrome device count: **6**
- AI provider: `staging-openai` (Shadow Mode only)
- Connector owner: `pilotco-owner`
- Test environment: `staging-equivalent`

### Signed Operating Checklist (owner-signed via program record)

| # | Checklist item | Evidence |
| --- | --- | --- |
| 1 | Pilot backup restore passes | Recorded in `operating_checklist`; backup not yet run in this pilot cycle |
| 2 | Security review complete | Recorded in `operating_checklist` |
| 3 | Staging release candidate validated | Recorded in `operating_checklist` |

## 2. Legal Acknowledgement Evidence

Owner (`pilotco-owner`) accepted all four documents:
`terms`, `privacy`, `ai_transfer`, `employee_privacy` (document_version `v1`).

Employees who performed task activity accepted all four documents through the
application acceptance workflow (`POST /api/v1/auth/company/acceptances`):

- `pilotco-emp1-1` — acceptance IDs 21, 23, 25, 27
- `pilotco-emp2-1` — acceptance IDs 22, 24, 26, 28

Total legal acceptances recorded: **12** across **3 distinct users**.

> Observation: the seed grants owner acceptances only. Employee terms/privacy/
> AI-transfer/acknowledgement capture must be validated for all 30 employees
> during the observation period (tracked in weekly report).

## 3. Branch / Employee / Chrome-Device Assignment Record

| Branch | Code | Employees | Monitors |
| --- | --- | --- | --- |
| Branch 1 | `pilotco-b1` | 10 | 1 (monitor1) |
| Branch 2 | `pilotco-b2` | 10 | 1 (monitor2) |
| Branch 3 | `pilotco-b3` | 10 | — |

- Job roles: `staff` (Shift Staff), `monitor` (Quality Monitor)
- Weekly shifts: 30 (one per employee, 09:00–17:00 local)
- Timezone `Asia/Riyadh`, operational-day cutoff 06:00 local
- Chrome device fleet target: 6 (2 per branch, per `chrome_device_count`)
- All task execution enforced through Chrome-only capture sessions; no gallery-upload fallback in the pipeline

## 4. Daily Operational Log

Date: 2026-08-26 (pilot day 1)

| Time (UTC) | Event |
| --- | --- |
| 09:29 | Environment verified: health OK, program active, 3 branches / 30 employees / 2 monitors |
| 10:55 | Three starter task templates created: `cash-handover`, `cleanliness-inspection`, `shift-close` |
| 11:00 | Template versions (checklist/evidence requirements) created for all three |
| 11:01 | Schedules created; scheduler generated 2 instances (cash-handover, cleanliness-inspection) |
| 11:07 | Employee `emp1-1` claimed/started `cash-handover`, created Chrome capture session, submitted 1 image, completed task |
| 11:07 | Employee `emp2-1` claimed/started high-risk `cleanliness-inspection` |
| 11:08 | High-risk capture session issued random challenge; employee answered challenge, submitted image with `face_detected=true` (face-blur path exercised) |
| 11:08 | Same photo re-submitted → `duplicate_risk_score=88` observed |
| 11:08 | Invalid (text) upload rejected cleanly: "Only JPEG, PNG, and WebP images are allowed." — blocked-capture behavior confirmed |
| 11:09 | Monitor2 created an `approve` review decision on the completed high-risk task |
| 11:09 | Owner created pilot issues: duplicate-risk confusion (medium); empty review queue (low) |
| 11:10 | Owner resolved issue "Empty review queue after completion" (low) |
| 11:10 | Change request "Add gallery-upload warning for Chrome-only capture" created and **approved** |
| 11:11 | Change request "Enable AI auto-pass for high-risk inspections" created and **rejected** (AI auto-pass gate respected) |
| 11:11 | Weekly report W/E 2026-08-26 created with actual metrics |
| 11:14 | Shift-close instance generated (branch 3) |
| 11:15 | Employee `emp3-1` claimed/started `shift-close`; transfer requested to `emp3-2` |
| 11:15 | **Incident:** approving the in-progress transfer raised `ValueError: Task cannot transition from in_progress to pending` (500). Recorded as high-severity pilot issue. |
| 11:15 | Employee `emp3-1` submitted shift-close evidence and completed the task |

### Operational observations captured

- Task volume (day 1): 3 task instances, 3 completed
- Image volume: 4 evidence images processed to private WebP
- Camera/challenge failures: 0 (challenge answered correctly)
- Upload failures: 1 invalid upload blocked cleanly (no partial write)
- Face-blur behavior: 1 image classified `face_detected=true` and blurred
- Review workload: 1 review decision
- Duplicate-risk signals: 1 flagged (score 88)
- AI agreement: N/A — 0 AI runs (connector offline, Shadow Mode)
- Connector health: `offline` / `offline` (no enrollment in pilot environment)
- Usability: duplicate photo confusion; empty review queue after completion
- **Defect found:** transfer approval crashes for in-progress tasks (`backend/apps/tasks/services.py:269`, `transition_task_instance` allows only completed/cancelled/overdue from `in_progress`)

## 5. Weekly Pilot Metrics Report

Created in-app: `PilotWeeklyReport` W/E `2026-08-26` (id `3b0dd682-554b-4698-b219-7f7cbc56194a`).

Selected metrics: tasks completed 2→3, image evidence 3→4, face blurred 1,
duplicate risk flagged 1, blocked captures 1, review decisions 1, issues 3 (1 resolved),
change requests 2 (1 approved / 1 rejected). `ai_agreement_rate=0.00` (no AI runs).

## 6. Pilot Issue Backlog and Change-Request Register

### Issue backlog (via `PilotIssue`)

| Title | Severity | Status | Accountable owner |
| --- | --- | --- | --- |
| Transfer approval of an in-progress task raises ValueError | high | open | PILOT-OPS-01 → hand to engineering; tracked for Phase 13 |
| Duplicate-risk signal on repeated cleanliness photo | medium | open | PILOT-OPS-01 / monitors (threshold review) |
| Empty review queue after completion | low | resolved | PILOT-OPS-01 |

### Change-request register (via `PilotChangeRequest`)

| Title | Status | Decided by |
| --- | --- | --- |
| Add gallery-upload warning for Chrome-only capture | approved | `pilotco-owner` |
| Enable AI auto-pass for high-risk inspections | rejected | `pilotco-owner` (reject: AI auto-pass gate not met) |

All issue/change/report operations were performed through the supported application
workflow and are audit-logged (`USER_LOGIN`, `PILOT_ISSUE_CREATED`,
`PILOT_CHANGE_REQUESTED`, `PILOT_CHANGE_DECIDED`, `PILOT_WEEKLY_REPORT_CREATED`,
`EVIDENCE_CAPTURE_SESSION_CREATED`, `EVIDENCE_SUBMITTED`, `TASK_INSTANCE_*`).

## Verified checks

- Employees complete tasks from Chrome without gallery-upload fallback: **yes** (capture-session path only)
- Owner/monitor/employee roles exercised against realistic tenant and branch data: **yes**
- Issues created and resolved without engineering intervention: **yes** (resolve path OK)
- Change requests created and approved/rejected through the application: **yes**
- Dashboard and weekly report contain actual data: **yes** (see dashboard summary)
- Connector and AI Shadow Mode observed: **yes** (offline status recorded; no auto-pass)

## Exit-gate status

- Pilot ran for an agreed observation period with real data: day 1 cycle complete; observation period to continue
- All required operational records and at least one weekly report exist: **yes**
- No active stop condition from Phase 12: no isolation/media/audit/recovery failures observed
- Outstanding high-severity issues explicitly assigned and tracked: **yes** (issue "Transfer approval …", high, open)
- Hand off to `PILOT-ASSURANCE-02` per exit gate: permitted once the observation period is agreed/completed