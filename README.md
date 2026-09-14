# Mhami

[![CI](https://github.com/dark-za/mhami/actions/workflows/ci.yml/badge.svg)](https://github.com/dark-za/mhami/actions/workflows/ci.yml)

Mhami is an MIT-licensed, self-hosted operations platform for evidence-driven work execution. One installation serves one organization. It helps the organization define role-based tasks, schedule them by branch, collect direct evidence, route exceptions for review, export records, and operate with audit, privacy, backup, and monitoring controls.

Mhami is not a hosted service and has no central support-account path into a deployment. The organization that runs it owns its infrastructure, accounts, and data. It includes a Django/DRF backend, React/TypeScript frontend, PostgreSQL, Redis, Celery, an AI connector boundary, Docker Compose environments, OpenAPI contracts, and CI quality gates.

## Capabilities

**Core (supported out of the box):**

- One locally provisioned organization, branches, and server-enforced access.
- Three roles: owner (full access), monitor (people and tasks in owner-assigned branches), and employee (their own assigned tasks).
- Task templates with versioned instructions, scheduled task instances, claims, starts, completions, cancellations, transfer requests, and employee exception requests.
- Evidence capture with privacy decisions, duplicate-risk metadata, media handling, and branch isolation.
- Review queues, review decisions, and owner-controlled review policy.
- Local encrypted backups and restore workflows, owner-controlled exports, and audit integrity controls.

**Optional infrastructure (requires operator configuration):**

- AI analysis in shadow mode: a fake local provider works without configuration; external OpenAI-compatible providers and the Organization Connector require explicit operator setup, credentials, and owner acceptance of the AI Transfer Notice.
- External S3-compatible backup upload: requires `BACKUP_EXTERNAL_URI` and related keys; without it only local encrypted artifacts are produced.
- Production hardening extras: NGINX security headers are included, but Prometheus/Grafana/Alertmanager dashboards and Let's Encrypt/TLS termination require the operator to configure `compose.prod.yml`, DNS, and certificates.

## Repository Layout

- `backend/` - Django modular monolith and REST API.
- `frontend/` - React browser application with Arabic/English support.
- `connector/` - FastAPI Organization Connector for signed AI-provider calls.
- `docs/` - architecture, installation, security, runbooks, ADRs, and data-handling notices.
- `infra/` - NGINX, monitoring, backup, security, and deployment support.
- `compose.yml` - shared local service topology.
- `compose.dev.yml` - development ports, mounts, and hot reload.
- `compose.prod.yml` - production overrides and hardening.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - one-organization model, Company compatibility boundary, branch scoping.
- [Roles and Access](docs/ROLES_AND_ACCESS.md) - owner, monitor, and employee roles with backend enforcement.
- [Installation](docs/INSTALLATION.md) - local deployment, environment setup, provisioning.
- [Getting Started](docs/GETTING_STARTED.md) - the first-owner setup and the normal owner, monitor, and employee workflow.

## Prerequisites

- Docker Engine and Docker Compose v2.
- Git.
- Python 3.13 for local backend work outside Docker.
- Node.js 24 and npm for local frontend work outside Docker.

Docker Compose is the supported deployment path on Linux, Windows (Docker
Desktop with WSL 2), and macOS (Docker Desktop). The optional connector runs
as a Linux container even when its host is Windows or macOS.

## Development Quick Start

1. Create the local environment file:

   ```bash
   cp .env.example .env
   ```

   PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Replace the placeholder secrets in `.env`. For local development, long random strings are enough:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

3. Start the stack:

   ```bash
   docker compose -f compose.yml -f compose.dev.yml up --build
   ```

4. Open the application:

   - Frontend: <http://localhost:5173>
   - API: <http://localhost:8000>
   - OpenAPI schema: <http://localhost:8000/api/schema/>
   - Swagger UI: <http://localhost:8000/api/docs/>

5. Provision the first and only organization owner. On a new installation,
   set a long random `INITIAL_SETUP_TOKEN` in `.env`, open `/setup`, and enter
   it to create the owner in the browser. The setup route closes permanently
   after success. Alternatively, the local command below prompts for the
   password so it is not placed in shell history:

   ```bash
   docker compose -f compose.yml -f compose.dev.yml exec api python manage.py provision_owner \
     --organization-name "Example Organization" \
     --owner-login-id owner \
     --owner-display-name "Organization Owner"
   ```

   This command fails safely once an organization exists. There is no public
   registration endpoint and no second organization can be provisioned by the
   application.

## Local Quality Checks

Backend:

```bash
cd backend
python -m compileall .
ruff check .
mypy .
python manage.py makemigrations --check --dry-run
python manage.py spectacular --validate
python manage.py check
pytest
```

Frontend:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
npm run test
npm run test:e2e
```

## Production Notes

Production deployment uses `compose.yml` plus `compose.prod.yml`:

```bash
docker compose -f compose.yml -f compose.prod.yml up --build -d
```

Before running production, provide real secret-manager backed values for:

- `DJANGO_SECRET_KEY`
- `AUDIT_HMAC_SECRET`
- `POSTGRES_PASSWORD`
- `METRICS_TOKEN`
- `BACKUP_ENCRYPTION_KEY`
- `DJANGO_ALLOWED_HOSTS`

External backup values (`BACKUP_EXTERNAL_URI`, `BACKUP_EXTERNAL_KEY_ID`, and
`BACKUP_EXTERNAL_KEYS`) are required only when the operator enables an
external S3-compatible backup destination. Do not use `.env.example` values in
production. See [Secret Management](docs/SECRET_MANAGEMENT.md), the
[deployment runbook](docs/runbooks/deployment.md), the [restore runbook](docs/runbooks/restore.md),
and [Public Release Plan](docs/PUBLIC_RELEASE_PLAN.md).

## Public Release Status

Mhami is open source under MIT and can be run on a local server or a provider
chosen by the organization. This repository does not provide a shared account
service or an upstream support-access mechanism. A production launch requires
operator review of the security controls. The notices under `docs/legal/`
explain the self-hosted data-responsibility model; they are not legal advice.

## License

Released under the MIT License. See [LICENSE](LICENSE).
