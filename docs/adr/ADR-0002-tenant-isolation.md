# ADR-0002: Tenant Isolation Model

## Status

Approved baseline.

## Context

The platform is multi-tenant and must prevent company and branch data leakage across users and support actors.

## Decision

Use company-scoped tenancy with branch-scoped authorization. Every sensitive query must filter by company first and branch second when applicable.

## Consequences

- Tenant escape becomes a testable defect instead of a hidden assumption.
- Role and branch membership must be explicit in every sensitive path.
