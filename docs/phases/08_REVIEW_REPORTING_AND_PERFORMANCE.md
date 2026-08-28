# Phase 08: Review, Reporting, and Performance Policies

## Status

Complete.

## Objective

Make the platform operationally useful without AI by delivering exception-focused monitor review, human decisions, corrective actions, owner reporting, and bounded performance policies.

## Entry Requirements

- Phase 07 is complete.
- Monitor decision types, performance-policy settings, evidence visibility, and report-restatement choices are approved.

## Scope

- Implement monitor queues for overdue work, retry/resubmission, employee issues, and non-AI evidence review where policy requires it.
- Implement monitor decisions: approve, approve despite alert, retry same task, mark missed, create corrective task, cancel where authorized, and override performance restrictions.
- Preserve original completion and append every later review decision.
- Implement owner dashboards for daily/branch completion, quality exceptions, and company trial status.
- Implement monitor dashboards for exceptions, overdue tasks, employee issues, and resubmissions.
- Implement productivity and quality calculations from final human outcomes, timely completion, missed/late results, and owner-defined template weights.
- Implement limited company policy settings for employee score visibility, historical report restatement, approved task weights, and predefined operational restrictions.
- Implement human-overridable restrictions: monitor approval requirement, sensitive-task claim restriction, extra evidence, and owner alerts.

## Explicit Exclusions

- No automatic employment punishment, account suspension, payroll action, or AI-only restriction.
- No general social feed, public leaderboard, or unrestricted gamification system.
- No predictive analytics.

## Required Software and Services

- `reviews`, `reporting`, and related policy services.
- PostgreSQL reporting queries or materialized strategies selected after pilot-load evidence.
- Celery default queue for non-interactive report preparation where required.

## Security and Data Requirements

- Human final decisions, not raw AI outputs, determine employee performance signals.
- Every policy change, restriction trigger, override, review decision, and report restatement is audited.
- Monitor access remains branch-scoped.
- Owners may see company-wide metrics; employee score visibility follows bounded company policy.

## Deliverables

- Review queue, evidence viewer, decision workflow, retry/missed/corrective flows.
- Owner and monitor reporting interfaces.
- Performance-policy configuration and restriction-override workflow.
- Audit and test documentation for report restatement and human override.

## Verification

- Monitor cannot review an unassigned branch.
- A late review does not erase original evidence or history.
- Score changes trace to final decisions and documented policy values.
- Restriction can be overridden by the monitor with a reason.
- Owner and monitor dashboards show only permitted company and branch information.

## Exit Criteria

- A monitor can manage all essential exceptions without AI.
- An owner can understand operational completion and quality trends.
- Performance indicators remain explainable, bounded, and human-governed.

## Stop Conditions

- AI alerts alone alter employee score or restrictions.
- Historical decisions are overwritten.
- Reporting leaks data across companies or branches.
