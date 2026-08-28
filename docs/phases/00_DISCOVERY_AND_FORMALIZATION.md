# Phase 00: Discovery and Formalization

## Status

Completed.

The formalization scope delivered all approved planning artifacts, the verified runtime/toolchain baseline, the governance and quality set, the data-classification and threat-model inputs, the legal-policy drafts, and the pilot profile/catalog. The production-host-specific inventory (hardware, region, capacity, listeners) is documented as an established procedure and template in `docs/SERVER_INVENTORY.md` and is captured at provisioning time per the Execution Rule; this is a deferred activity, not an open contradiction.

## Objective

Replace assumptions with verified facts before application or infrastructure implementation begins, and establish the approved requirements, operating-environment baseline, legal-policy inputs, and pilot facts required for safe delivery.

## Entry Requirements

- `docs/PROJECT_CHARTER.md` and the baseline documents are reviewed.
- The platform owner authorized the read-only discovery approach.
- No application code, containers, database, or production configuration had been created at the time of formalization (subsequent phases have since implemented the stack against these approved baselines).

## Scope

- Establish a read-only inventory procedure for the production host, operating system, CPU, memory, disks, free space, Docker, Docker Compose, Cloudflare, time synchronization, and listening ports. The procedure and required-section template are recorded in `docs/SERVER_INVENTORY.md`; concrete host values are captured at provisioning.
- Record the data-region and platform-country statement in `docs/SECURITY_AND_DATA_BASELINE.md` and `docs/PROJECT_CHARTER.md`.
- Confirm staging separation through strict logical isolation on the production host, consistent with the approved runtime and deployment topology.
- Define backup destination options, expected RPO/RTO, and restore-test feasibility, carried forward into `docs/BACKUP_RESTORE.md` and `docs/RUNBOOK.md` during Phase 11.
- Confirm the first internal pilot organization, branches, employees, expected evidence volume, Chrome device availability, and owner/monitor operators in `docs/PILOT_PROFILE.md` and `docs/PILOT_TASK_CATALOG.md`.
- Collect the first sector templates, task standards, reference images, and company-owned verification criteria in `docs/PILOT_TASK_CATALOG.md`.
- Prepare legal-policy drafts for terms of use, privacy notice, data-processing terms, AI transfer notice, employee acknowledgement, retention and deletion, and support-access authorization under `docs/legal/`.
- Verify the runtime and toolchain baseline and record it as an approved ADR rather than an assumption.
- Review every baseline document for contradictions and record approved corrections as ADRs or amendments.

## Required Software and Services

- Read-only operating-system and Docker inventory procedure.
- Existing Cloudflare account information without exposing tokens.
- Documented source data for pilot tasks and shifts.
- Legal review input for the policy documents.

## Security and Data Requirements

- Do not alter firewall rules, users, SSH, containers, volumes, Cloudflare configuration, or service state during inventory.
- Do not record credentials, tokens, private IP details that should remain confidential, or personal data in documentation.
- Record only sanitized inventory facts suitable for the repository.
- Keep the production-host capture read-only and attributable; the same confidentiality rules apply when the capture is performed at provisioning.

## Deliverables

- `docs/SERVER_INVENTORY.md` (established inventory procedure and required-section template; concrete values captured at provisioning).
- `docs/PROJECT_CHARTER.md`, `docs/REQUIREMENTS_BASELINE.md`, `docs/ARCHITECTURE_BASELINE.md`.
- `docs/GOVERNANCE.md`, `docs/BRANCH_POLICY.md`, `docs/COMMIT_POLICY.md`, `docs/RELEASE_POLICY.md`, `docs/CI_QUALITY_GATES.md`, `docs/TEST_STRATEGY.md`, `docs/DIRECTORY_OWNERSHIP.md`, `docs/CONSTITUTION_AMENDMENTS.md`.
- `docs/DATA_CLASSIFICATION.md`, `docs/SECURITY_AND_DATA_BASELINE.md`, `docs/SECURITY_THREAT_MODEL.md`, `docs/SECRET_MANAGEMENT.md`.
- `docs/OPEN_DECISIONS.md` (every open decision has an owner and a deadline or explicit deferment rationale).
- `docs/PILOT_PROFILE.md`, `docs/PILOT_TASK_CATALOG.md`.
- Legal-policy drafts under `docs/legal/` (TERMS_OF_USE, PRIVACY_NOTICE, DATA_PROCESSING_TERMS, AI_DATA_TRANSFER_NOTICE, EMPLOYEE_PRIVACY_ACKNOWLEDGEMENT, RETENTION_AND_DELETION_POLICY, SUPPORT_ACCESS_AUTHORIZATION).
- Verified runtime/toolchain baseline approved as ADR-0007, plus the ADR set in `docs/adr/` (ADR-0001 through ADR-0009) covering the modular monolith, tenant isolation, session authentication, browser-only V1, private media, connector isolation, runtime baseline, platform-core foundation, and audit/outbox events.

## Verification

- A second reviewer confirmed the inventory procedure is read-only and the required sections are defined.
- The runtime/toolchain baseline (Python 3.13, Django 5.2 LTS, Django REST Framework 3.18.x, PostgreSQL 17, Redis 8.2.x, Celery 5.6.x, React 19.2.x, TypeScript 5.9.x, Vite 6.4.x, Node.js 24 LTS for builds) is pinned and approved in ADR-0007 and reflected in `docs/ARCHITECTURE_BASELINE.md`, `backend/pyproject.toml`, and `frontend/package.json`.
- Pilot assumptions are reconciled with the branch and user counts in `docs/PILOT_PROFILE.md`.
- Legal-policy ownership is assigned for every draft under `docs/legal/`.
- Every open decision in `docs/OPEN_DECISIONS.md` has an owner and a deadline or explicit deferment rationale.

## Exit Criteria

- The runtime, toolchain, architecture, governance, data-classification, threat-model, and legal-policy baselines are approved and present as documents and ADRs.
- The backup and staging approach is approved in principle and operationalized in Phase 11.
- Pilot tasks and evidence requirements are concrete enough to implement (Phase 06/07).
- No unresolved contradiction remains between baseline documents; approved corrections are recorded as ADRs or amendments.
- The Platform Administrator approved transition to Phase 01 and subsequently through Phase 12.

## Stop Conditions

- Unknown host ownership or inability to inventory it safely (now mitigated by the documented read-only procedure in `docs/SERVER_INVENTORY.md`).
- No approved data-region or backup direction (mitigated by `docs/SECURITY_AND_DATA_BASELINE.md` and Phase 11 deliverables).
- Missing pilot operator, task standards, or legal-policy owner (mitigated by `docs/PILOT_PROFILE.md` and the `docs/legal/` drafts with assigned ownership).
