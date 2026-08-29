# ADR-0012: MCP OAuth And Scope Topology

## Status

Draft for implementation.

## Context

The Django backend does not currently host OAuth infrastructure. Implementing a correct authorization server would add a large security surface.

## Decision

Use a delegated identity provider as the default OAuth topology for external MCP clients. The `mcp-gateway` validates external tokens and maps them to Mhami `AgentGrant` records. Django receives only internal HMAC-signed calls from the gateway.

Scopes are fixed in a backend registry. Grants may store only known scopes. Deprecated scopes remain readable for existing grants but are not available for new grants.

ADR-0012 must define the token validation mode before production use: local JWT verification with JWKS caching or live token introspection. It must also define expected `audience` / resource values and tenant mapping.

## Consequences

- OAuth dependencies live in `mcp-gateway` unless a later ADR proves backend need.
- Backend authorization is still defensive: every internal agent call verifies the grant, expiry, revocation, tenant, and required scope.
- Scope typos fail validation instead of becoming silent permissions.
