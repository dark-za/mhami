# Phase 03: Platform Core

## Status

Completed.

## Objective

Establish the reusable platform boundary that every future module relies on: module discovery, configuration, feature flags, errors, tracing, audit, outbox, health, and policy primitives.

## Entry Requirements

- Phase 02 is complete and quality gates pass.
- Module manifest format and dependency rules are approved.

## Scope

- Implement module manifests, registry discovery, compatibility validation, dependency validation, and module health status.
- Implement standardized API errors and namespaced error codes.
- Implement request ID propagation through HTTP, jobs, audit, and events.
- Implement structured JSON logging with module-specific loggers.
- Implement transactional outbox and idempotent event consumption primitives.
- Implement append-only audit-event infrastructure with integrity metadata.
- Implement configuration, limited feature flags, policy settings primitives, and system health endpoints.
- Implement bootstrap API contract foundations, without role-specific business screens.

## Required Software and Services

- Django, DRF, PostgreSQL, Redis, Celery, structlog, and drf-spectacular.
- Test tools for unit, integration, migration, and permission tests.

## Security and Data Requirements

- Audit records cannot be mutated through ordinary APIs.
- Health endpoints reveal only appropriate detail by authorization level.
- Error responses never expose traces or secrets.
- Outbox writes occur in the same database transaction as the business change.

## Deliverables

- `platform_core` and `audit` module contracts.
- Module manifest and health-check framework.
- Logging, request ID, error, audit, event, and feature-flag documentation.
- OpenAPI foundation.
- Core test suite and architecture ADRs.

## Verification

- Registry rejects circular or incompatible dependencies.
- Request ID appears in a request, audit event, and background event.
- Duplicate outbox delivery does not duplicate side effects.
- Audit mutation attempts fail.
- Core health endpoints distinguish live, ready, and module status.

## Exit Criteria

- New modules can be added through a documented contract.
- The platform can trace, audit, and safely publish a generic business event.
- No task-specific business logic is present in the core.

## Stop Conditions

- Any module bypasses the registry, audit, or standardized authorization foundation.
- Asynchronous events are published outside a reliable transaction boundary.
