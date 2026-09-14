# Architecture

## One-Organization Model

Each Mhami installation serves exactly one organization. There is no multi-tenant routing, no company-code login, no public registration, and no central support path. The organization that runs the installation owns its infrastructure, accounts, and data.

The first owner is provisioned locally by the installation operator using `python manage.py provision_owner`. No second organization can be created through the application.

## Company as Internal Compatibility Boundary

The database table previously used for multi-tenant company routing (`Company`) is retained as an internal compatibility boundary. Foreign keys, ORM references, and historical audit records still reference it. Product-facing terminology uses "organization" or "installation." It remains a deliberate compatibility boundary until a separately approved migration demonstrates that removing it is worthwhile.

## Branch Scoping

Branch isolation is enforced server-side on every data access. The authorization layer resolves the authenticated user's role and branch assignments before any object lookup. Frontend navigation and bootstrap data are display hints only; they never grant access.

## Backend Enforcement

The Django backend is the single enforcement source for authorization. Every API endpoint, service, and queryset applies role checks and branch scoping. The frontend trusts the backend's bootstrap response for navigation and feature visibility.

## No Central Service

Mhami has no shared control plane, no upstream telemetry, and no hosted backend. There is no central support-account path into a deployment. The deployment operator is responsible for infrastructure, updates, backups, and security.

## Runtime Topology

```text
Internet (optional TLS termination)
  -> NGINX (or operator-chosen reverse proxy)
     -> React static build
     -> /api -> Gunicorn -> Django
                           -> PostgreSQL
                           -> Redis
                           -> Celery workers
                           -> private media storage

Organization private AI endpoint (optional)
  <- Organization Connector (Linux Docker, outbound authenticated channel)
  <- Platform AI Gateway
```

The organization chooses its own hosting provider, TLS termination, backup destination, and AI provider configuration. Docker Compose is the supported deployment baseline.

## Supported vs Optional Infrastructure

- **Supported out of the box:** Django API, React frontend, PostgreSQL, Redis, Celery, private media storage, local encrypted backups, owner-controlled exports, and audit integrity. No external service is required to run the application.
- **Optional, operator-configured:** External AI provider and Organization Connector (requires credentials, endpoint, and owner acceptance of the AI Transfer Notice; a fake local provider is used otherwise), external S3-compatible backup upload (requires BACKUP_EXTERNAL_URI etc.), Lets Encrypt/ACME TLS, and Prometheus/Grafana/Alertmanager. These are documented in infra/ and compose.prod.yml but are not provisioned automatically and must be verified by the operator before production use.
