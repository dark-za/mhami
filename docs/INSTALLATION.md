# Installation

## Requirements

- Docker Engine and Docker Compose v2.
- Git.
- Python 3.13 for local backend work outside Docker.
- Node.js 24 and npm for local frontend work outside Docker.

Docker Compose is the supported deployment method on Linux, Windows with
Docker Desktop and WSL 2, and macOS with Docker Desktop. Python and Node are
only required for development outside Docker.

## Quick Start

1. Clone the repository and create the environment file:

   ```bash
   cp .env.example .env
   ```

   PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Replace the placeholder secrets in `.env` with secure random values:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

   Leave `DJANGO_CSRF_TRUSTED_ORIGINS` empty for the standard same-origin
   Nginx deployment. Set it to each exact HTTPS browser origin only when the
   frontend and API are intentionally hosted on different origins.

   For browser-based first setup, also set `INITIAL_SETUP_TOKEN` to a unique
   random value. Keep it with the server operator; it is required only while
   no organization exists and is never returned by the API.

3. Start the stack:

   ```bash
   docker compose -f compose.yml -f compose.dev.yml up --build
   ```

4. Verify services are running:

   - Frontend: <http://localhost:5173>
   - API: <http://localhost:8000>
   - OpenAPI schema: <http://localhost:8000/api/schema/>

   Development ports bind only to `127.0.0.1`; they are not intended for LAN
   or public access. Containers still communicate over the internal Compose
   network. Use the production deployment below for access from other devices.
   During `compose up`, the frontend waits for the API health check to pass.
   Docker daemon restarts do not enforce Compose dependency ordering; transient
   connection errors can still occur while the services recover.

5. Provision the first organization owner using one of these secure paths:

   - **Browser setup:** open <http://localhost:5173/setup>, then enter the
     organization details, owner credentials, and `INITIAL_SETUP_TOKEN`. The
     endpoint is CSRF-protected, rate-limited, and closes permanently after it
     creates the one organization.

   - **Local command:**

   ```bash
   docker compose -f compose.yml -f compose.dev.yml exec api python manage.py provision_owner \
     --organization-name "Example Organization" \
     --owner-login-id owner \
     --owner-display-name "Organization Owner"
   ```

   The command prompts for the password so it is not placed in shell history.
   This command fails safely once an organization exists. There is no public
   registration endpoint: setup is a one-time server-operator action, and no
   second organization can be provisioned by the application.

## Production Deployment

Use `compose.yml` plus `compose.prod.yml`:

```bash
docker compose -f compose.yml -f compose.prod.yml up --build -d
```

Before running production, provide real secret-manager backed values for all
placeholder environment variables. Do not use `.env.example` values in
production.

**Optional infrastructure (requires operator configuration):** External S3-compatible backup upload (`BACKUP_EXTERNAL_URI`, `BACKUP_EXTERNAL_KEY_ID`/`BACKUP_EXTERNAL_KEYS`), external AI provider / Organization Connector (endpoint, credentials, and owner acceptance of the AI Transfer Notice), and TLS/Let's Encrypt or Prometheus/Grafana alerting are *not* provisioned automatically. They require explicit operator setup and verification using `docs/runbooks/`, `docs/SECRET_MANAGEMENT.md`, and `infra/`.

Refer to the existing runbooks for database migration, backup configuration,
secret management, and deployment verification procedures. Before production
launch, the operator verifies its secrets, TLS, backup/restore process, and
applicable internal and legal requirements. The source repository does not
claim legal or regulatory compliance.

## Database Migrations

Migrations run automatically as part of container startup. To run them manually:

```bash
docker compose exec api python manage.py migrate --noinput
```

## Verification

After provisioning, log in with the owner credentials and verify:

- The frontend loads and displays the correct organization name.
- Branch creation and user management work as expected.
- Task templates can be created and assigned.
- An employee can see only assigned work and submit a request for an exception;
  a monitor assigned to the branch can decide it.

Continue with [Getting Started](GETTING_STARTED.md) for the owner setup order
and day-to-day workflow.
- The API responds correctly at `/api/health/live` and `/api/health/ready`.
