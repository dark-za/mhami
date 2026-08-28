# Docker Assets

Container build and run conventions for the platform.

## Backend image (`../backend/Dockerfile`)

- `python:3.13-slim`, installs `libmagic1` (python-magic runtime dependency)
  and `requirements.txt`.
- Creates `/app/media` and `/app/staticfiles` and chowns them (plus
  `/app/backend`) to the non-root `appuser`; the container runs as `USER appuser`.
- These paths match Django settings exactly (`MEDIA_ROOT=/app/media`,
  `STATIC_ROOT=/app/staticfiles`).
- Default CMD runs the Django dev server; production overrides the command with
  `migrate && gunicorn config.wsgi:application`.

## Frontend image (`../frontend/Dockerfile`)

- `development` stage: `npm ci` + Vite dev server.
- `build` stage: `npm run build`.
- `production` stage: `nginx:1.27-alpine`, copies `nginx.conf` and the built
  SPA into `/usr/share/nginx/html`.

## Production hardening

- API container runs `read_only: true` with a `/tmp` tmpfs; media writes go to
  the `media-data` volume at `/app/media`.
- Containers run non-root; the Docker socket is never mounted.
- Secrets are injected via environment (never baked into images).