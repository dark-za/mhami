# ADR-0006: Tenant Connector Isolation

## Status

Approved baseline.

## Context

Tenant-specific AI providers may live in private or local networks. The shared SaaS runtime must not gain arbitrary network access to those environments.

## Decision

Use a tenant-owned Linux Docker connector with authenticated outbound communication for private or local AI connectivity.

## Consequences

- Private tenant networks remain isolated from the shared SaaS runtime.
- Connector enrollment, health, versioning, and revocation become explicit requirements.
- Provider integration can vary by tenant without user-uploaded executable code.
