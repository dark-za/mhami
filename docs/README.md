# Documentation Authority

## Status

These documents describe the current self-hosted Mhami edition: its
architecture, installation, roles, security practices, and operating runbooks.

## Precedence

1. `ARCHITECTURE.md`, `INSTALLATION.md`, and `ROLES_AND_ACCESS.md` describe
   the supported product and its setup.
   `GETTING_STARTED.md` is the practical entry point for a new operator.
   `MCP_ACCESS.md` documents owner-controlled MCP grant issuance and client
   request authentication.
2. `SECRET_MANAGEMENT.md`, `SECURITY_EXCEPTIONS.md`, and the root `SECURITY.md`
   describe security responsibilities and disclosure.
3. `runbooks/` contains the procedures needed to operate a deployment.
4. `adr/` documents architecture decisions; `contracts/` defines external
   integration boundaries.
5. `legal/` contains simplified data-handling notices, not legal advice.

## Change Control

Document a material change to roles, branch isolation, AI behavior, retention,
evidence handling, or security before implementation. Use an ADR for a
foundational architecture decision.

## Documentation Areas

- `contracts/`: implementation-independent contracts for external boundaries.
- `GETTING_STARTED.md`: first-install and daily workflow guide.
- `adr/`: architecture decision records.
- `legal/`: simplified data-handling notices; not legal advice.
- `runbooks/`: operational procedures.
- `templates/`: reusable documentation templates.
- Repository practices are expressed through the root policy documents.
