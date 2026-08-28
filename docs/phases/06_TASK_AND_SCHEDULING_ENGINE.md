# Phase 06: Task and Scheduling Engine

## Status

Complete.

## Objective

Implement the generic operational execution engine: versioned task definitions, branch and shift-aware scheduling, assignment, start, transfer, overdue behavior, and auditable state transitions.

## Entry Requirements

- Phase 05 is complete.
- Pilot company task catalog, job roles, shifts, and operational-day settings are available.
- Task-template versioning and overdue-policy rules are approved.

## Scope

- Implement task templates, template versions, checklist definitions, evidence requirements, reference instructions, risk designation, and task weights.
- Implement task schedules with daily fixed-time, weekly fixed-time, and shift-relative recurrence.
- Implement named-user, role-pool, and monitor-distributed assignment modes by template.
- Generate idempotent task instances through a central scheduler.
- Implement explicit task start and atomic claim behavior.
- Implement task transfer requests, assigned-user approval flow, and monitor override.
- Implement branch-visible task lists with more restrictive evidence visibility.
- Implement overdue alert behavior and per-template post-deadline policy.
- Implement cancellation by owner or monitor with required reason and permanent history.
- Implement employee transfer effects: cancel and recreate affected scheduled work while preserving historical records.

## Explicit Exclusions

- No attendance clock, payroll calculation, staff optimization, or full workforce scheduling.
- No arbitrary cron editor.
- No direct evidence upload or AI business logic in this phase.

## Required Software and Services

- Django models, PostgreSQL transactions and constraints, Celery Beat central scheduling trigger, Celery default worker, and frozen-time test tooling.

## Security and Data Requirements

- Every task query applies company and branch authorization.
- Task status changes only through a state-machine service.
- Task template revisions do not overwrite historical standards.
- Company and branch policy settings are constrained choices, not executable rules.

## Deliverables

- `tasks` module models, migrations, services, APIs, manifest, health check, audit events, and documentation.
- Task-template configuration screens and role-appropriate task lists.
- Scheduler and task-transfer workflow.
- Starter generic template library and the three approved restaurant reference templates.

## Verification

- Daily, weekly, and shift-relative tasks generate correctly across timezone and operational-day cutoff boundaries.
- Re-running the scheduler does not duplicate instances.
- Concurrent task claims cannot assign the same work twice.
- Employee transfer, task transfer, cancellation, overdue, and invalid state transitions are tested.
- A user cannot inspect or mutate another company or unauthorized branch task.

## Exit Criteria

- A company can configure and execute tasks without evidence or AI.
- Historical task standards are explainable from their template version.
- The core task engine is useful and safe independently of later evidence modules.

## Stop Conditions

- Any status can be edited directly.
- Scheduler generation is non-idempotent.
- Shift-relative work is implemented as an undeclared attendance system.
