# Test Strategy

## Status

Planning baseline. Detailed suites are added in the implementation phases.

## Required Test Layers

- Unit tests for domain services and policy calculations.
- Integration tests for database constraints, transactions, outbox, jobs, and storage.
- API tests for contracts, errors, authentication, and authorization.
- Permission tests for tenant, branch, role, support, export, and media scope.
- Scheduler tests using frozen time, timezone, shift, and operational-day cases.
- Media tests for signature, size, quarantine, face derivative, duplicate risk, and capture sessions.
- AI tests with a fake provider and staging-only provider contract tests.
- Chrome browser tests for task capture and administrative workflows.
- Security, migration, backup restore, failure injection, and release smoke tests.

## Quality Rule

A later phase cannot declare itself complete merely because the happy path works. Its phase document defines its required test evidence.
