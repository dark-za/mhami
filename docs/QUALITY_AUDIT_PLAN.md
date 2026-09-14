# Quality Audit and Improvement Plan

Date: 2026-09-06
Status: In progress; no release approval implied.

## Product Contract

Mhami is a self-hosted application for one organization per installation.
The owner administers the installation; monitors manage people and tasks only
in owner-assigned branches; employees work on their own tasks. Arabic is the
default UI language, with complete English support. AI and MCP are optional,
owner-controlled integrations. Existing installation data must be preserved.

## Evidence Rules

- Audit current files, including uncommitted work; HEAD alone is not the baseline.
- Findings require a file/line reference, trigger, expected and actual behavior,
  severity, and a reproducible check. Separate observations from hypotheses.
- Independent agents perform read-only reviews first. The orchestrator validates
  each claim before accepting it or assigning implementation.
- Never include local secrets, private runtime data, or credentials in reports.
- Do not reset databases, remove volumes, publish, or commit unrelated changes.
- Passing mocked browser tests does not prove an installed backend workflow.

## Work Packages

| ID | Owner / lane | Scope | Required evidence |
| --- | --- | --- | --- |
| A1 | OpenCode / complex | Authentication, first-owner setup, branch authorization, tasks, evidence, MCP/AI boundaries | Concrete abuse paths and existing enforcement/tests |
| A2 | OpenCode / ui | Arabic/English, RTL, errors, forms, routing, role-specific screens, accessibility | Component references, visible triggers, uncovered states |
| A3 | OpenCode / tests | Runtime, migrations, persistence, backup/restore, dependencies, CI, installation docs | Commands/contracts and reproducible mismatches |
| V1 | Orchestrator | Verify agent claims and run independent baseline gates | Command results and accepted/rejected findings |
| F1 | Bounded implementer assignments + orchestrator review | Fix confirmed high-impact defects in dependency order | Scoped diff and regression proof |
| V2 | Orchestrator | Re-run affected gates; inspect rendered flows | Verified results and residual gaps |

## Execution Order

1. Record workspace state and effective free-model delegation lanes.
2. Dispatch A1-A3; gather local baseline evidence while they run.
3. Run available gates: backend ruff/mypy/Django checks/migration check/schema
   validation/coverage; connector checks; frontend typecheck/build/Vitest/browser
   tests; dependency vulnerability audits. Record unavailable gates explicitly.
4. Validate findings against actual code and negative/positive tests. Classify
   Critical, High, Medium, or Low; reject unsupported claims with reasons.
5. Implement confirmed security and data-integrity defects first, then broken
   user workflows and CI regressions, then bounded usability/documentation fixes.
6. Verify the changed contracts and preserve role boundaries and stored data.
7. Publish an evidence report containing accepted findings, applied changes,
   rejected findings, unverified areas, and prioritized remaining improvements.

## Completion Conditions

- Each work package has a recorded outcome, not just an agent's completion claim.
- Applied fixes are reviewed and pass checks appropriate to their scope.
- Remaining release limitations are explicit; no claim of zero vulnerabilities,
  full production readiness, or universal OS/browser support without evidence.
- Proposed larger product changes include impact and acceptance criteria.
