# Phase 12 Weekly Metrics Workbook

> **UNFILLED TEMPLATE - NOT EVIDENCE.** Populate from actual pilot observation records, not seed data or automated-test results. Each metric requires a query, report, audit, or other source link that can be independently checked.

## Record Control

| Field | Value |
| --- | --- |
| Weekly report ID | `P12-WEEK-<pilot-program-id>-<YYYYMMDD>` |
| PilotProgram ID | `<uuid>` |
| Week start / week ending (local) | `<YYYY-MM-DD> / <YYYY-MM-DD>` |
| Timezone / operational-day cutoff | `<IANA timezone> / <HH:MM>` |
| Report preparer / reviewer account IDs | `<account-id> / <account-id>` |
| In-app `PilotWeeklyReport` ID | `<uuid>` |
| Source dashboard/report link | `<link>` |

## Population and Capacity

| Metric ID | Metric | Definition | Target/baseline | Actual | Unit | Branch breakdown link | Source evidence link | Owner | Acceptance criterion / status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-MET-01` | Active participants | Active owner, monitors, and employees during the week. | `<target>` | `<value>` | `participants` | `<link>` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-02` | Task volume | Scheduled, completed, late, missed, and completion rate. | `30-60 per branch/day expected` | `<values>` | `tasks / %` | `<link>` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-03` | Evidence image volume | Image count by branch/day and peak period. | `150-400 per branch/day peak expected` | `<value>` | `images` | `<link>` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-04` | Storage growth | Start/end storage, net growth, bytes per image/task, projected capacity. | `<baseline>` | `<values>` | `bytes` | `<link>` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |

## Capture, Privacy, and Review

| Metric ID | Metric | Definition | Actual | Unit | Source evidence link | Owner | Acceptance criterion / status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-MET-05` | Camera failures | Failed camera/capture-session attempts divided by capture attempts; include blocked gallery fallback attempts. | `<value>` | `count / %` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-06` | Upload reliability | Failed uploads, retries, successful retries, and failure rate. | `<values>` | `count / %` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-07` | Face-blur behavior | Face-detected, blurred derivative created, false-positive/negative reports, and exceptions. | `<values>` | `count / %` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-08` | Review workload | Decisions, queue age, decision latency, rework, missed decisions, and monitor coverage. | `<values>` | `count / duration` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-09` | Duplicate-risk | Signals, score distribution, confirmed duplicates, false positives, and resulting action. | `<values>` | `count / %` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |

## AI and Connector

| Metric ID | Metric | Definition | Actual | Unit | Source evidence link | Owner | Acceptance criterion / status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-MET-10` | AI run coverage | Runs by risk level and status (`completed`, `needs_review`, `failed`). | `<values>` | `count / %` | `<link>` | `<connector-owner>` | `Shadow Mode only` |
| `P12-MET-11` | AI agreement | `(runs agreeing with human decision / all comparable runs) * 100`; explain denominator exclusions. | `<value>` | `%` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-12` | AI error analysis | Provider failure, malformed result, human disagreement, and face-detection error categories. | `<analysis>` | `narrative/count` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-13` | Auto-pass control | Runs with `auto_pass_activated=True`; must remain zero. | `<value>` | `count` | `<link>` | `<account-id>` | `zero; STOP if nonzero` |
| `P12-MET-14` | Connector reliability | Health status, uptime, outages, mean outage duration, and evidence-submission fallback outcome. | `<values>` | `% / duration` | `<link>` | `<connector-owner>` | `<criterion / pass-fail>` |

## Usability, Issues, and Weekly Decision

| Metric ID | Metric | Definition | Actual | Source evidence link | Owner | Acceptance criterion / status |
| --- | --- | --- | --- | --- | --- | --- |
| `P12-MET-15` | Usability feedback | Coded employee/monitor/owner feedback, support requests, confusion themes, and affected workflow. | `<values>` | `<link>` | `<account-id>` | `<criterion / pass-fail>` |
| `P12-MET-16` | Issue/change flow | Opened/resolved issues by severity and requested/approved/rejected changes. | `<values>` | `<07 link>` | `<account-id>` | `<criterion / pass-fail>` |

| Weekly conclusion | Value |
| --- | --- |
| Success-measure assessment | `<evidence-based statement>` |
| Capacity findings | `<evidence-based statement>` |
| AI agreement/error analysis | `<evidence-based statement>` |
| Required actions / accountable owners / due dates | `<references>` |
| Reviewed by / review evidence | `<account-id / link>` |

**STOP `P12-STOP-02`:** Any observed AI auto-pass activation is a stop condition. **STOP `P12-STOP-01`:** Any tenant isolation, media-protection, audit-integrity, or recovery failure is a stop condition. Do not label a weekly report accepted while an active STOP marker lacks linked resolution evidence.
