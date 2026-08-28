# Data Classification

## Status

Not started. Complete during Phase 00 with legal-policy input.

## Purpose

Classify every data category by sensitivity, controller/processor role, access scope, storage, retention, exportability, and deletion behavior.

## Initial Categories

| Category | Examples | Initial handling direction |
| --- | --- | --- |
| Account data | Login identifier, display name, company contact | Private; role-scoped; audit changes. |
| Organization data | Company, branch, shifts, job roles, policies | Tenant-scoped; export by authorized role. |
| Operational data | Tasks, checklists, decisions, reports | Tenant and branch scoped; append-only history. |
| Evidence media | Camera images, blurred derivatives, numbers, notes | Private storage; strict authorization; no public URLs. |
| AI configuration | Provider endpoint, model, credentials | Owner-only; encrypted secrets; never exported or logged. |
| Audit and security data | Request IDs, actions, support access | Append-only; protected access; retention policy. |
| Export artifacts | ZIP, CSV, PDF | Temporary, authorized, expiring, and audited. |
