# ADR-0008: Platform Core Foundation

## Status

Approved baseline.

## Context

The platform needs module discovery, request tracing, health reporting, standardized errors, outbox primitives, and a place for shared policy and configuration before product modules start.

## Decision

Implement these concerns in the reusable platform core rather than scattering them across feature modules.

## Consequences

- Future modules depend on explicit core primitives.
- API errors, health, and event behavior stay standardized.
- Shared infrastructure can evolve without rewriting product modules.
