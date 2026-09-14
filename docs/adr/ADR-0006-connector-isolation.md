# ADR-0006: Tenant Connector Isolation

## Status

Approved baseline.

## Context

An organization’s AI provider may live in a private or local network. The
Mhami installation must not gain arbitrary network access to that environment.

## Decision

Use an organization-operated Linux Docker connector with authenticated outbound
communication for private or local AI connectivity.

## Consequences

- Private organization networks remain isolated from the application runtime.
- Connector enrollment, health, versioning, and revocation become explicit requirements.
- Provider integration can vary by installation without user-uploaded executable code.
