# Phase 10: Exports and Integration Boundaries

## Status

Complete.

## Objective

Provide authorized tenant data portability and formal extension boundaries without allowing uncontrolled external access, storage, notifications, or code execution.

## Entry Requirements

- Phase 09 is complete.
- Export access matrix and data-classification rules are approved.
- Storage-capacity direction is known from Phase 00 inventory and pilot estimates.

## Scope

- Implement asynchronous export jobs for ZIP media archives, CSV structured data, and PDF summaries.
- Enforce export authority: owner for company-wide data, monitor for assigned branches, support only with active company authorization.
- Filter exports by authorized company, branches, date ranges, and permitted data categories.
- Deliver exports through short-lived, authenticated downloads and audit every request, generation, download, and expiry.
- Define approved integration boundaries for future notification providers, external storage destinations, and public APIs without implementing them.
- Define connector-independent provider and storage extension review process.

## Explicit Exclusions

- No Google Drive, OneDrive, customer file-server, S3/R2, or automated archival integration in V1.
- No SMS, WhatsApp, Telegram, email, or arbitrary notification provider in V1.
- No public tenant API token or unrestricted third-party API in V1.
- No user-uploaded webhook code, plugins, scripts, or custom executable adapters.

## Required Software and Services

- Celery default worker for asynchronous packaging.
- Private temporary export storage with expiration and cleanup.
- PDF rendering approach selected through ADR.

## Security and Data Requirements

- Export authorization is checked at request time and delivery time.
- Exports are tenant- and branch-scoped, logged, expiring, and unavailable through public permanent URLs.
- Sensitive values, credentials, raw unblurred images, internal logs, and secrets are excluded from exports.
- Support export actions require current tenant authorization and named support-actor attribution.

## Deliverables

- `exports` module with jobs, APIs, cleanup, audit, and authorization tests.
- Owner and monitor export user flows.
- Integration extension policy and future-provider review checklist.
- Data portability documentation.

## Verification

- A monitor cannot export another branch or company data.
- A revoked support grant invalidates export capability.
- Download links expire and cannot be reused without authentication.
- Large exports do not block HTTP requests.
- Export contents match access scope and exclude sensitive technical data.

## Exit Criteria

- Authorized users can retrieve the data they are entitled to without exposing it publicly.
- Deferred integrations have explicit safe contracts rather than ad hoc future shortcuts.

## Stop Conditions

- Export packaging runs in an HTTP request.
- A static or permanent public export URL exists.
- An integration requires arbitrary code execution from a tenant UI.
