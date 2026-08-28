# Phase 12 Resilience-Test Evidence Index

> **UNFILLED TEMPLATE - NOT EVIDENCE.** This index records actual controlled exercises and their source evidence. Test only with authorized safe fixtures where required. Passing automated tests alone does not prove a real-pilot exercise.

## Record Control

| Field | Value |
| --- | --- |
| Evidence index ID | `P12-RES-<pilot-program-id>-<YYYYMMDD>` |
| PilotProgram ID | `<uuid>` |
| Exercise coordinator account ID | `<account-id>` |
| Reviewer account ID | `<account-id>` |
| Index reviewed date (UTC) | `<ISO-8601>` |
| Related incident-response runbook | [`../runbooks/incident-response.md`](../runbooks/incident-response.md) |

## Exercise Index

| Exercise ID | Required path | Scope / safe-fixture authorization | Planned / executed (UTC) | Executor / observer account IDs | Steps and result summary | Evidence links | Acceptance criterion | Status | STOP/issue ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P12-RES-01` | Tenant and branch isolation | `<tenant/branch scope and authorization>` | `<planned / actual>` | `<ids>` | `<summary>` | `<audit/test/report links>` | No cross-company or unauthorized cross-branch access, mutation, or export. | `planned / pass / fail / blocked` | `<id or none>` |
| `P12-RES-02` | Support authorization boundary | `<named support request and scope>` | `<planned / actual>` | `<ids>` | `<summary>` | `<authorization/audit links>` | Access is tenant-scoped, audited, and revoked after use; no unauthorized export. | `planned / pass / fail / blocked` | `<id or none>` |
| `P12-RES-03` | Connector outage fallback | `<connector/branch scope>` | `<planned / actual>` | `<ids>` | `<summary>` | `<health/audit/task links>` | Evidence submission continues while connector is offline; no unsafe acceptance. | `planned / pass / fail / blocked` | `<id or none>` |
| `P12-RES-04` | AI failure fallback | `<risk-level and safe evidence scope>` | `<planned / actual>` | `<ids>` | `<summary>` | `<AI/task/review links>` | Evidence submission continues; AI remains Shadow Mode; no automatic acceptance. | `planned / pass / fail / blocked` | `<id or none>` |
| `P12-RES-05` | Export authorization | `<authorized owner/monitor/support scope>` | `<planned / actual>` | `<ids>` | `<summary>` | `<export/audit links>` | Authorized, tenant/branch-scoped export only; sensitive data exclusions verified. | `planned / pass / fail / blocked` | `<id or none>` |
| `P12-RES-06` | 90-day read-only tenant path | `<safe fixture and lifecycle authorization>` | `<planned / actual>` | `<ids>` | `<summary>` | `<state/export/audit links>` | Read-only export path works with safe fixtures; operational activity remains blocked. | `planned / pass / fail / blocked` | `<id or none>` |
| `P12-RES-07` | Backup and restore | `<backup artifact/recovery environment>` | `<planned / actual>` | `<ids>` | `<summary>` | `<backup/restore verification links>` | Restore verifies database, media, configuration, and tenant-state counts. | `planned / pass / fail / blocked` | `<id or none>` |

## Evidence Quality Check

- [ ] Every executed exercise has a timestamp, executor, observer/reviewer, scope, result, and immutable/auditable source link.
- [ ] Every failure has an issue ID, accountable owner, containment action, and retest or approved disposition.
- [ ] Safe-fixture use and any support authorization are linked where relevant.
- [ ] Connector and AI failure results explicitly show whether evidence submission continued.
- [ ] No exercise result is marked `pass` when source evidence is missing.

**STOP:** A failed tenant isolation, media protection, audit integrity, recovery, or unauthorized auto-pass exercise is an active Phase 12 STOP marker. Stop affected pilot activity, follow the incident runbook, and link the incident and disposition in `07_ISSUE_CHANGE_DISPOSITION_REGISTER.md`.
