# ADR-0009: Audit and Outbox Events

## Status

Approved baseline.

## Context

The platform needs append-only business history and safe asynchronous event publication that survives transaction failure.

## Decision

Use append-only audit events and a transactional outbox model for asynchronous domain events.

## Consequences

- Business history is traceable and tamper-evident.
- Event publication becomes idempotent and recoverable.
- Consumers must treat delivery as at-least-once.
