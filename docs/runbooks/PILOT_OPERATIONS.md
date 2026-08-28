# Pilot Operations Runbook

Operational steps for setting up and running the Phase 12 internal pilot against a staging-equivalent deployment. This runbook turns the Phase 12 gate document (`docs/phases/12_INTERNAL_PILOT.md`) into concrete, repeatable actions. Treat all pilot evidence as production-like personal and operational data.

Use the unfilled, non-evidence handoff templates in [`../pilot-evidence/`](../pilot-evidence/08_PHASE1_HANDOFF_CHECKLIST.md) to capture actual pilot records, source links, and STOP-condition handling. They do not replace legal review, human authorization, or the Phase 12 exit decision.

## 1. Preconditions

- Dev stack is running (see `README.md`): API on `http://127.0.0.1:8000`, frontend on `http://127.0.0.1:5173`, Postgres 17, Redis 8.2.
- Backend migrations are applied (`python manage.py migrate --noinput`).
- The `pilot` module is enabled for the target company (bootstrap `enabled_modules` includes `pilot`).

## 2. Seed the pilot company

Use the management command to create the company, branches, roles, users, shifts, and the pilot program in one step:

```bash
docker compose -f compose.yml -f compose.dev.yml exec -T api python manage.py seed_pilot --company pilotco
```

Defaults create:

- Company `pilotco` ("Pilot Coffee Co"), industry restaurants_and_cafes, 60-day trial.
- 3 branches (`pilotco-b1`, `pilotco-b2`, `pilotco-b3`), Asia/Riyadh, 06:00 operational-day cutoff.
- 1 owner (`pilotco-owner`, role Owner), 2 monitors (`pilotco-monitor1`/`monitor2`, role Monitor), 30 employees (10 per branch, role Employee).
- Job roles `staff` and `monitor`.
- Legal acceptance records for terms, privacy, AI transfer, and employee privacy acknowledgement.
- Weekly shifts for employees.
- An active `PilotProgram` matching the branch/employee targets.

The seed is idempotent-guarded: re-running without `--reset` fails with a clear error. Use `--reset` to tear down the existing company cleanly before reseeding:

```bash
docker compose -f compose.yml -f compose.dev.yml exec -T api python manage.py seed_pilot --company pilotcode --reset
```

Optional flags: `--name`, `--branches`, `--employees-per-branch`, `--password`.

## 3. Verify the seeded environment

Confirm the API is healthy and the pilot dashboard loads for the owner:

```bash
curl.exe --fail http://127.0.0.1:8000/api/health/live
```

Expected pilot endpoints (owner/monitor only for mutations):

- `GET /api/v1/pilot/program` — program profile.
- `GET /api/v1/pilot/dashboard` — weekly evidence/AI/connector summary and counts.
- `GET/POST /api/v1/pilot/weekly-reports` — weekly metrics.
- `GET/POST /api/v1/pilot/issues` and `PATCH /api/v1/pilot/issues/{id}` — issue tracking and resolution.
- `GET/POST /api/v1/pilot/change-requests` and `PATCH /api/v1/pilot/change-requests/{id}` — change requests and approve/reject.

## 4. Chrome-only browser policy

- All pilot task execution uses Chrome. Enforce the Chrome-only policy via the tenant branding/login experience; do not allow gallery-upload fallback for evidence.
- Verify employees can complete a task from Chrome only (no gallery fallback).
- Monitor blocked-capture attempts in the evidence pipeline.

## 5. Terms, privacy, and acknowledgement

- Confirm the seeded legal acceptances appear for the owner. For employees, ensure terms, privacy notice, employee privacy acknowledgement, and AI transfer acceptance are recorded before they complete tasks.
- Treat any missing acceptance as a pilot issue (record via `POST /api/v1/pilot/issues`).

## 6. Operate the pilot loop

1. **Monitors** process alerts, issues, retries, missed decisions, and corrections; resolve issues via the PilotPanel (or `PATCH /api/v1/pilot/issues/{id}`).
2. **Owners** review branch completion, quality exceptions, performance policies, and trial status; record a weekly report (`POST /api/v1/pilot/weekly-reports`).
3. **Change control**: record change requests and approve/reject them explicitly (`PATCH /api/v1/pilot/change-requests/{id}`). Do not bypass audit.
4. **Fault handling**: a connector outage or AI failure must not halt evidence submission; verify fallback continues.

## 7. Exit-readiness checklist

- Employees complete tasks from Chrome without gallery fallback.
- Monitors resolve exceptions without engineering intervention.
- Owners see weekly branch and quality trends.
- Export and 90-day read-only tenant path tested with safe fixtures.
- High-severity defects resolved or have approved release decisions.
- Capacity, recovery, legal-policy, and support findings recorded in the weekly report and backlog.

## 8. Stop conditions

Stop the pilot immediately if: tenant isolation or media protection fails, audit integrity or recovery is broken, or the pilot cannot operate without engineering intervention for routine workflows.
