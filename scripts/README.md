# Scripts

## Compose Contracts

Run `python scripts/test_compose.py` from the repository root. Requires Python
and Docker Compose v2, but does not start containers or require a running daemon.
It resolves both Compose variants with an empty env file and validation-only
required values, then checks development loopback bindings, API health ordering,
internal proxy routing, and production port isolation. CI runs the same checks.

Backend-specific checks and maintenance commands live in `backend/scripts/`
and Django management commands. See the installation guide and runbooks before
running operations that change application data.
