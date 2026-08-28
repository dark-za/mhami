# ADR-0003: Secure Cookie Sessions

## Status

Approved baseline.

## Context

The primary interface is browser-based and single-domain oriented. Logout, revocation, and CSRF protection are simpler with cookie-based sessions than with JWT for this use case.

## Decision

Use secure HttpOnly cookie sessions with CSRF protection for the web application.

## Consequences

- Simpler session revocation and logout.
- Standard browser security controls apply.
- API and frontend authentication stay aligned.
