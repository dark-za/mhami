# ADR-0010: MCP Protocol Version

## Status

Draft for implementation.

## Context

Mhami will expose a remote Model Context Protocol surface for approved agents. The gateway must not depend on stateful MCP sessions because new work is expected to target the 2026-07-28 stateless protocol model.

## Decision

Build `mcp-gateway` against MCP 2026-07-28 with Streamable HTTP only. Every request must be self-contained. Cross-request state must use explicit server-minted handles or durable Mhami records, never implicit MCP sessions.

Write-capable tools must require a caller-stable `idempotency_key`. The key is part of the tool schema and is validated before any backend mutation.

## Consequences

- `stdio` is out of scope for the hosted gateway.
- The gateway can run behind a load balancer without sticky sessions.
- Older MCP clients require a compatibility decision before they are supported.
