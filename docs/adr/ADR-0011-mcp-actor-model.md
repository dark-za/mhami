# ADR-0011: MCP Actor Model

## Status

Draft for implementation.

## Context

Existing service-layer functions operate on a real Mhami user and tenant membership. Rewriting every service function to accept a second synthetic agent actor would create broad risk.

## Decision

An MCP action executes as the user that owns the active `AgentGrant`. The business service receives that existing user as its actor. Agent-specific attribution is stored outside business tables in `AgentActionLog`.

Audit and reporting surfaces must read through `apps.audit.services.get_audit_trail()` so records can expose whether an action was executed directly by a human or through an agent.

## Consequences

- Existing tenant and role checks remain authoritative.
- Agent actions cannot exceed the granting user's privileges.
- Reports that bypass `get_audit_trail()` are considered incorrect and must fail review or CI checks.
