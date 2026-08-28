# Delivery Roadmap

## Execution Rule

Phases are sequential. A phase cannot begin implementation until every exit criterion in its predecessor is met, documented, and reviewed. A later phase may refine a detail only through documented change control; it may not silently reverse an approved baseline.

## Phase Index

| Phase | Name | Primary outcome | Status |
| --- | --- | --- | --- |
| 00 | Discovery and Formalization | Verified environment facts and approved planning documents | Completed |
| 01 | Repository and Governance Foundation | Governed repository, documentation, ADR, and quality workflow | Completed |
| 02 | Runtime and Development Foundation | Runnable local foundation with isolated development tooling | Completed |
| 03 | Platform Core | Module boundaries, audit, outbox, settings, health, and common controls | Completed |
| 04 | Identity, Tenancy, and SaaS Lifecycle | Tenant registration, roles, sessions, MFA, trial, legal acceptance, and scopes | Completed |
| 05 | Web Shell and Design System | Chrome web shell, bilingual UX, tenant branding, and in-app notifications | Completed |
| 06 | Task and Scheduling Engine | Versioned templates, shifts, schedules, instances, transfers, and state transitions | Completed |
| 07 | Evidence and Privacy Pipeline | Live camera capture, secure media pipeline, face derivatives, and task discussion | Completed |
| 08 | Review, Reporting, and Performance Policies | Monitor workflow, human decisions, owner insight, and bounded performance rules | Completed |
| 09 | AI Gateway and Tenant Connector | Structured AI verification, Shadow Mode, and Linux connector | Completed |
| 10 | Exports and Integration Boundaries | Authorized exports and documented deferred integration extension points | Completed |
| 11 | Security, Observability, Backup, and Recovery | Production security and operational resilience evidence | Completed |
| 12 | Internal Pilot | Measured internal multi-branch validation | Complete — staging pilot evidence captured; owner sign-off pending |
| 13 | Production Readiness and Controlled Launch | Release candidate, rollout, and support readiness | Not started |

## Gate Categories

Every phase document contains the following gates:

- Objective and business outcome.
- Entry requirements and dependencies.
- Approved scope and explicit exclusions.
- Required modules, tools, and services.
- Data, authorization, security, and audit rules.
- Documentation and implementation deliverables.
- Required verification.
- Exit criteria and stop conditions.

## Current Position

Discovery and formalization (Phase 00) is complete: the runtime/toolchain baseline, architecture, governance, data-classification, threat-model, legal-policy drafts, pilot profile/catalog, and the ADR set (ADR-0001 through ADR-0009) are approved and present. Phases 01 through 12 are complete in staging evidence; Phase 13 is a planned future gate that may not begin until the owner records the Phase 12 exit decision.
