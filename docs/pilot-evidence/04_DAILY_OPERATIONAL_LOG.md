# Phase 12 Daily Operational Log

> **UNFILLED TEMPLATE - NOT EVIDENCE.** Enter observed events only, with source links. Do not reconstruct activity from memory or use seed/rehearsal records as real-user evidence.

## Record Control

| Field | Value |
| --- | --- |
| Daily log ID | `P12-DAY-<pilot-program-id>-<YYYYMMDD>` |
| Pilot day / local date / timezone | `<day-number> / <YYYY-MM-DD> / <IANA timezone>` |
| PilotProgram ID | `<uuid>` |
| Duty owner account ID | `<account-id>` |
| Monitor account IDs | `<account-ids>` |
| Start / end time (UTC) | `<ISO-8601> / <ISO-8601>` |
| Source dashboard/audit link | `<link>` |

## Start-of-Day Gate

| Check ID | Check | Result | Checked by | Time (UTC) | Evidence link | Stop/issue ID |
| --- | --- | --- | --- | --- | --- | --- |
| `P12-DAY-GATE-01` | Active participants are complete in legal reconciliation. | `pass / fail` | `<account-id>` | `<ISO-8601>` | `<03 link>` | `<id or none>` |
| `P12-DAY-GATE-02` | Chrome devices required for planned shifts are approved. | `pass / fail` | `<account-id>` | `<ISO-8601>` | `<02 link>` | `<id or none>` |
| `P12-DAY-GATE-03` | AI is Shadow Mode; auto-pass is disabled. | `pass / fail` | `<account-id>` | `<ISO-8601>` | `<system link>` | `<id or none>` |
| `P12-DAY-GATE-04` | No uncleared Phase 12 STOP marker affects planned operation. | `pass / fail` | `<account-id>` | `<ISO-8601>` | `<01 link>` | `<id or none>` |

## Event Log

| Event ID | Time (UTC) | Branch ID | Role/account ID | Event type | Observation or action | Task/evidence/review/issue ID | Source evidence link | Owner | Outcome / follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-EVT-<YYYYMMDD>-001` | `<ISO-8601>` | `<uuid>` | `<role / account-id>` | `task / capture / alert / retry / review / correction / support / issue / change / stop` | `<factual observation>` | `<identifier>` | `<link>` | `<account-id>` | `<result>` |

## Daily Counts and Observations

| Metric | Count/value | Source link | Notes |
| --- | --- | --- | --- |
| Scheduled / completed / late / missed tasks | `<counts>` | `<link>` | `<by branch if material>` |
| Evidence images / storage added | `<counts / bytes>` | `<link>` | `<by branch if material>` |
| Camera failures / blocked captures | `<counts>` | `<link>` | `<cause>` |
| Upload failures / retries / successful retries | `<counts>` | `<link>` | `<cause>` |
| Face-detected / blurred / blur exceptions | `<counts>` | `<link>` | `<outcome>` |
| Review decisions / queue age / escalations | `<counts / duration>` | `<link>` | `<outcome>` |
| Duplicate-risk signals / confirmed duplicates | `<counts>` | `<link>` | `<outcome>` |
| AI runs / failures / human disagreements | `<counts>` | `<link>` | `Shadow Mode only` |
| Connector health / outage duration | `<status / duration>` | `<link>` | `<fallback observed>` |
| Usability feedback / support requests | `<count>` | `<link>` | `<coded themes>` |

## End-of-Day Review

| Item | Result | Evidence link | Accountable owner | Due date |
| --- | --- | --- | --- | --- |
| Routine workflow completed without engineering intervention | `yes / no` | `<link>` | `<account-id>` | `<date or n/a>` |
| New issue/change entries linked | `yes / no` | `<07 link>` | `<account-id>` | `<date>` |
| STOP marker triggered or still active | `<none / ID>` | `<link>` | `<account-id>` | `<date>` |
| Daily log reviewed by owner/monitor | `pending / reviewed` | `<approval/audit link>` | `<account-id>` | `<date>` |

**STOP:** Immediately pause affected activity and preserve source records if tenant isolation, media protection, audit integrity, recovery, or unauthorized AI auto-pass fails. Also pause an affected participant's activity for missing legal acceptance or an unapproved capture device. Record the STOP ID and escalation in the event log and `07_ISSUE_CHANGE_DISPOSITION_REGISTER.md`.
