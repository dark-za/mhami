# Mhami

[![CI](https://github.com/dark-za/mhami/actions/workflows/ci.yml/badge.svg)](https://github.com/dark-za/mhami/actions/workflows/ci.yml)

Mhami is a multi-tenant operations platform for evidence-driven work execution. It helps organizations define role-based tasks, schedule them by branch, collect direct evidence, route exceptions for review, export records, and operate with audit, privacy, backup, and monitoring controls.

The current release is a runnable product foundation, not a hosted service. It includes a Django/DRF backend, React/TypeScript frontend, PostgreSQL, Redis, Celery, a tenant AI connector, Docker Compose environments, OpenAPI contracts, and CI quality gates.

## Capabilities

- Multi-tenant companies, branches, memberships, and role-scoped access.
- Task templates, scheduled task instances, claims, starts, completions, cancellations, and transfer requests.
- Evidence capture with privacy decisions, duplicate-risk metadata, media handling, and branch isolation.
- Review queues, review decisions, and owner-controlled review policy.
- AI analysis in shadow mode with a fake local provider and an OpenAI-compatible provider boundary.
- Exports, local encrypted backups, external S3-compatible backup upload, and restore workflows.
- Pilot management models for charters, weekly reports, issues, change requests, and exit decisions.
- Production Compose hardening, NGINX security headers, Prometheus/Grafana/Alertmanager, and Let's Encrypt support.

## Repository Layout

- `backend/` - Django modular monolith and REST API.
- `frontend/` - React browser application with Arabic/English support.
- `connector/` - FastAPI tenant connector for signed AI-provider calls.
- `docs/` - architecture, security, runbooks, legal placeholders, and delivery references.
- `infra/` - NGINX, monitoring, backup, security, and deployment support.
- `compose.yml` - shared local service topology.
- `compose.dev.yml` - development ports, mounts, and hot reload.
- `compose.prod.yml` - production overrides and hardening.

## Prerequisites

- Docker Engine and Docker Compose v2.
- Git.
- Python 3.13 for local backend work outside Docker.
- Node.js 24 and npm for local frontend work outside Docker.

## Development Quick Start

1. Create the local environment file:

   ```bash
   cp .env.example .env
   ```

2. Replace the placeholder secrets in `.env`. For local development, long random strings are enough:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
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

5. Seed a pilot workspace when you need demo data:

   ```bash
   docker compose -f compose.yml -f compose.dev.yml exec api python manage.py seed_pilot --company pilotco --password "replace-with-local-demo-password"
   ```

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
```

## Production Notes

Production deployment uses `compose.yml` plus `compose.prod.yml`:

```bash
docker compose -f compose.yml -f compose.prod.yml up --build -d
```

Before running production, provide real secret-manager backed values for:

- `DJANGO_SECRET_KEY`
- `AUDIT_HMAC_SECRET`
- `MFA_ENCRYPTION_KEYS`
- `POSTGRES_PASSWORD`
- `METRICS_TOKEN`
- `BACKUP_ENCRYPTION_KEY`
- `BACKUP_EXTERNAL_URI`
- `BACKUP_EXTERNAL_KEY_ID`
- `BACKUP_EXTERNAL_KEYS`
- `DJANGO_ALLOWED_HOSTS`

Do not use `.env.example` values in production. See [docs/SECRET_MANAGEMENT.md](docs/SECRET_MANAGEMENT.md), [docs/RUNBOOK.md](docs/RUNBOOK.md), and [docs/PUBLIC_RELEASE_PLAN.md](docs/PUBLIC_RELEASE_PLAN.md).

## Public Release Status

Mhami is source-available and runnable, but a production launch still requires organization-specific legal approval, real pilot evidence, owner sign-offs, and deployment credentials. Legal documents under `docs/legal/` are placeholders until reviewed and approved by qualified counsel.

## License

Released under the MIT License. See [LICENSE](LICENSE).
