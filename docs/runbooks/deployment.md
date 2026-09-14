# Deployment Runbook

Promote a validated release candidate from staging to production using the `compose.prod.yml` topology (Postgres 17, Redis 8.2, API on Gunicorn, frontend/NGINX, Celery workers). Never deploy directly from development to production.

## Inputs

- A release candidate validated by CI (`ruff`, `mypy`, `pytest`, `npm` build/test, dependency scans) and exercised on a staging-equivalent deployment.
- TLS certificates provisioned externally and mounted at `/etc/nginx/certs` (see `frontend/nginx.conf`). The Nginx listener reads the stable Certbot paths `/etc/nginx/certs/live/mhami/fullchain.pem` and `/etc/nginx/certs/live/mhami/privkey.pem`. The optional Certbot profile can issue or renew that named certificate, but the first HTTPS start still requires a reachable HTTP webroot and operator-provided DNS/email configuration. Without valid certificate files, the 443 listener will not start.

## Steps

1. Record the release artifact identity: Git commit SHA, version, build time, and schema version. Keep artifacts immutable.
2. Back up the current production database and media (see `restore.md` / `infra/backup`).
3. Verify `DJANGO_SECRET_KEY` and `AUDIT_HMAC_SECRET` are present in the production secret store.
4. Stage the build: `docker compose -f compose.yml -f compose.prod.yml up -d --build`.
5. Run migrations as part of startup (`python manage.py migrate --noinput`), never manually outside a deployment window.
6. Verify readiness endpoints: `GET /api/health/live` and `GET /api/health/ready` (DB + Redis), then scrape the token-protected `/api/v1/metrics` endpoint for worker, queue, disk, and backup freshness.
7. Verify frontend over HTTPS: root 200, `/api` proxy reaches the API, security headers from `infra/nginx/security-headers.conf` are present.
8. Verify owner login using controlled test accounts.
9. Create initial organization users and branches as needed.

## Rollback

Keep the previous release artifact intact. To roll back, redeploy the previous artifact (database migrations are forward-only; a rollback that reverses a migration requires the documented migration-reversal path, not a silent downgrade).
