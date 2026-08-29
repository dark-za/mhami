# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes |

## Reporting a Vulnerability

Report vulnerabilities through a private GitHub security advisory for this repository, or contact the project maintainer through the repository owner account. Do not open public issues for suspected vulnerabilities that expose exploit details, secrets, tenant data, or deployment information.

Please include:

- Affected component and version or commit SHA.
- Reproduction steps.
- Impact assessment.
- Any relevant logs, screenshots, or proof-of-concept snippets with secrets removed.

## Security Scope

In scope:

- Authentication and session handling.
- Tenant isolation and branch scoping.
- Evidence and media protection.
- Export and backup access controls.
- Connector request signing and replay protection.
- AI-provider egress boundaries.
- Production Compose and NGINX security controls.

Out of scope:

- Social engineering.
- Denial-of-service testing against systems you do not own.
- Attacks requiring compromised maintainer credentials.
- Legal interpretations of placeholder policy documents.

## Production Guidance

Production deployments must use a secret manager or an equivalent protected runtime mechanism for all secrets. Never deploy with `.env.example` values. Run CI, dependency scans, migration checks, and deployment smoke tests before promoting a release.
