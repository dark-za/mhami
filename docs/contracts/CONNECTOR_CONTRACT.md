# Tenant Connector Contract

## Purpose

Allow a tenant technical team to use private, local, or custom AI endpoints while protecting the shared SaaS platform from direct private-network access.

## V1 Runtime

- Linux Docker only.
- Installed and operated by the tenant technical team.
- Connects through an authenticated outbound channel.
- Reports version, compatibility, and health to the platform.

## Responsibilities

- Receive authenticated, tenant-scoped AI analysis jobs.
- Call the configured tenant provider endpoint using tenant-managed credentials.
- Return only the validated structured result and safe operational metadata.
- Enforce connector version compatibility, revocation, timeouts, and least privilege.

## Prohibitions

- No general remote shell, arbitrary command execution, file browsing, or network proxy behavior.
- No connector access across tenant boundaries.
- No provider credential return to the platform or browser.
- No unreviewed protocol adapter loaded dynamically from the tenant UI.

## Required Future Decisions

- Enrollment and key-rotation design.
- Mutual authentication mechanism.
- Update strategy and compatibility window.
- Resource limits and local log-retention policy.
