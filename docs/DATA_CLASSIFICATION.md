# Data Classification

## Status

Current guidance for the self-hosted edition. The organization operating the
server applies its own retention and legal requirements.

## Purpose

Classify every data category by sensitivity, controller/processor role, access scope, storage, retention, exportability, and deletion behavior.

## Initial Categories

| Category | Examples | Initial handling direction |
| --- | --- | --- |
| Account data | Login identifier, display name, organization contact | Private; role-scoped; audit changes. |
| Organization data | Organization, branch, shifts, job roles, policies | Organization-scoped; export by authorized role. |
| Operational data | Tasks, checklists, decisions, reports | Organization and branch scoped; append-only history. |
| Evidence media | Camera images, blurred derivatives, numbers, notes | Private storage; strict authorization; no public URLs. |
| AI configuration | Provider endpoint, model, credentials | Owner-only; encrypted secrets; never exported or logged. |
| Audit and security data | Request IDs and actions | Append-only; protected access; retention policy. |
| Export artifacts | ZIP, CSV, PDF | Temporary, authorized, expiring, and audited. |
