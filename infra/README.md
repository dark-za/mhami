# Infrastructure

Operational assets for the modular operations platform. The runtime topology is
declared in the Compose files at the repository root and built from the images
in `backend/Dockerfile` and `frontend/Dockerfile`.

## Compose topology

| Compose file | Intended use |
| --- | --- |
| `../compose.yml` | Base services shared by dev and prod (db, redis, api, frontend). |
| `../compose.dev.yml` | Local development: hot-reload API (runserver), Vite dev server on 5173. |
| `../compose.prod.yml` | Production: migrate + Gunicorn, Celery worker/beat services, TLS-terminating NGINX, read-only API with writable media volume. Use a separate project name for staging/validation. |

## Key paths (must match Django settings)

- `MEDIA_ROOT = BASE_DIR / "media"` -> `/app/media` (volume `media-data`)
- `STATIC_ROOT = BASE_DIR / "staticfiles"` -> `/app/staticfiles`
- `BASE_DIR` resolves to `/app` (repo root inside the backend image)

## Areas

- `./nginx/` - security header snippet and gateway guidance.
- `./monitoring/` - health endpoints and Alertmanager rules.
- `./docker/` - container build/run conventions.
- `./backup/` - backup/restore guidance.
- `./cloudflare/` - edge/tunnel guidance.

The deployment topology must never bind the Docker socket, runs containers
non-root, and keeps the API read-only (writable media via volume) in production
per `../compose.prod.yml`.