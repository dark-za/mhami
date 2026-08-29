# ADR-0014: MCP Audit And Logging

## Status

Draft for implementation.

## Context

`AuditEvent` is append-only and hash-protected. Adding columns or changing the canonical hash payload is unnecessary for the first MCP implementation and would increase risk.

## Decision

Use the existing `AuditEvent.request_id` as the correlation key for MCP actions. `AgentActionLog` stores grant id, tool name, action status, idempotency key, argument hash, and the same request id.

`record_audit_event()` remains the official audit writer. Other helpers that need an audit row should call this service or be explicitly allowlisted and tested.

`get_audit_trail()` is the official read surface for audit reporting. It annotates audit rows with `executed_via` and agent metadata when an `AgentActionLog` exists for the same request id.

## Consequences

- The audit hash chain remains unchanged.
- One agent call may map to multiple audit rows through a shared request id.
- CI can block direct audit creation outside approved audit internals.
