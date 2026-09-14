# Tenant Connector Contract

## Purpose

Allow the organization operating an installation to use private, local, or
custom AI endpoints without exposing its private network to the application.

## V1 Runtime

- Linux Docker only.
- Installed and operated by the organization’s technical team.
- Connects through an authenticated outbound channel.
- Reports version, compatibility, and health to the platform.

## Responsibilities

- Receive authenticated, organization-scoped AI analysis jobs.
- Call the configured organization provider endpoint using operator-managed credentials.
- Return only the validated structured result and safe operational metadata.
- Enforce connector version compatibility, revocation, timeouts, and least privilege.

## Prohibitions

- No general remote shell, arbitrary command execution, file browsing, or network proxy behavior.
- No connector access outside the installation’s organization boundary.
- No provider credential return to the platform or browser.
- No unreviewed protocol adapter loaded dynamically from the browser UI.

## Required Future Decisions

- Enrollment and key-rotation design.
- Mutual authentication mechanism.
- Update strategy and compatibility window.
- Resource limits and local log-retention policy.
