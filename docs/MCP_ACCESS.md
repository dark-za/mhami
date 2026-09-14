# MCP Access

Mhami exposes a small MCP JSON-RPC endpoint at `/api/v1/agent/mcp`. Requests
are rejected until an owner creates an agent grant from the MCP Access page.

## Owner controls

- Only the owner can create, view, and revoke grants.
- Each grant belongs to one active organization user, a client fingerprint,
  selected scopes, and an expiry time.
- The generated grant secret is displayed once at creation. Mhami stores only
  a password hash of it; it cannot be recovered later. Revoke and reissue a
  grant when the secret is lost or exposed.
- A grant never expands the user it belongs to: owner access covers the
  organization, monitor access is limited to assigned branches, and employee
  access is limited to tasks assigned to that employee.

## Client request requirements

Every request must use HTTPS and include:

- `X-Agent-Grant-Id`: the grant UUID.
- `X-Mhami-Client-Fingerprint`: the fingerprint recorded for the grant.
- `X-Mhami-Grant-Secret`: the one-time secret issued to the owner.
- `X-Mhami-Timestamp`: an ISO-8601 timestamp with a timezone.
- `X-Mhami-Nonce`: a unique nonce that is not reused within the configured
  replay window.
- `X-Request-ID`: a UUID used for correlation.
- `X-Mhami-Signature`: `sha256=<HMAC-SHA256>` using the grant secret.

The signed canonical payload is the newline-delimited timestamp, nonce,
grant ID, request ID, client fingerprint, and SHA-256 digest of the request
body. Replays, expired timestamps, inactive users, expired grants, revoked
grants, mismatched fingerprints, and invalid secrets are rejected.

## Scope and data boundaries

Scopes allow only the matching tool. They are further constrained by the
grant user's current role and branch access on every call. Changing or
deactivating that user immediately prevents future MCP calls. Tool actions use
an idempotency key bound to the canonical hash of their arguments.

Do not place a grant secret in a browser, source repository, shell history,
or support ticket. Keep it in the operating organization's secret manager.
