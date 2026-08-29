# ADR-0013: MCP Internal HMAC Contract

## Status

Draft for implementation.

## Context

Mhami already uses HMAC, timestamps, and nonces for the tenant connector. MCP internal traffic needs the same replay resistance, but backend deployments may run multiple replicas.

## Decision

All `mcp-gateway` to backend calls must be signed with:

- `X-Mhami-Signature`
- `X-Mhami-Timestamp`
- `X-Mhami-Nonce`
- `X-Agent-Grant-Id`
- `X-Request-Id`

The canonical string signs the timestamp, nonce, grant id, request id, and SHA-256 body digest. Backend replay protection must use Redis or another shared cache with TTL, not process memory.

Errors crossing this boundary use `{ "error": { "code": "...", "message": "...", "request_id": "..." } }`.

## Consequences

- Gateway failures remain isolated from normal browser APIs.
- Every agent call can be correlated through `request_id`.
- Multi-replica backend deployments reject replayed nonces consistently.
