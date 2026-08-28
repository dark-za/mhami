# ADR-0001: Modular Monolith

## Status

Approved baseline.

## Context

The platform needs clear module boundaries, a single primary database, simpler deployment, and a lower failure surface than a distributed microservice system.

## Decision

Use a modular monolith with explicit internal module contracts instead of microservices for V1.

## Consequences

- Simpler deployment and testing.
- Easier transactional consistency.
- Lower internal network complexity.
- Module extraction remains possible later if technically justified.
