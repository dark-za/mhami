# ADR-0003: Secure Cookie Sessions

## Status

Approved baseline.

## Context

The primary interface is browser-based and single-domain oriented. Logout, revocation, and CSRF protection are simpler with cookie-based sessions than with JWT for this use case.

## Decision

Use secure HttpOnly cookie sessions with CSRF protection for the web application.

Login is explicitly CSRF-protected even before a session exists. Browser clients
first request `GET /api/v1/bootstrap`, retain the resulting `csrftoken` cookie,
then send its value in `X-CSRFToken` with `POST /api/v1/auth/login`. A successful
login rotates the CSRF token; subsequent mutations must read the updated cookie.
The standard deployment uses one origin. Separate trusted frontend origins must
be explicitly configured through `DJANGO_CSRF_TRUSTED_ORIGINS`.

## Consequences

- Simpler session revocation and logout.
- Standard browser security controls apply.
- API and frontend authentication stay aligned.
