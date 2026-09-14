# Test Strategy

## Status

Current quality strategy. The automated commands are listed in the root README
and enforced by CI.

## Required Test Layers

- Unit tests for domain services and policy calculations.
- Integration tests for database constraints, transactions, outbox, jobs, and storage.
- API tests for contracts, errors, authentication, and authorization.
- Permission tests for organization, branch, role, export, and media scope.
- Scheduler tests using frozen time, timezone, shift, and operational-day cases.
- Media tests for signature, size, quarantine, face derivative, duplicate risk, and capture sessions.
- AI tests with a fake provider and staging-only provider contract tests.
- Chrome browser tests for task capture and administrative workflows.
- Security, migration, backup restore, failure injection, and release smoke tests.

## Quality Rule

Changes are accepted only when the relevant automated checks and targeted
regression tests pass.
