# NGINX Assets

This directory documents NGINX hardening for the platform gateway. The gateway
itself is built from `../frontend/Dockerfile` using `../frontend/nginx.conf`.

## security-headers.conf

Canonical security header set for the platform (deny framing, nosniff, referrer
policy, permissions policy, HSTS preload). Phase 13 requires these headers to be
applied in production.

The header set is carried inline into both server blocks of
`../frontend/nginx.conf` because that image builds from the `./frontend`
context and `../infra` is not part of the build context. Keep this snippet and
the inline copy in `../frontend/nginx.conf` in sync.

## Gateway behavior (frontend/nginx.conf)

- Port 80: ACME `/.well-known/acme-challenge/` webroot at `/var/www/certbot`,
  HTTP-to-HTTPS redirect for everything else, and `/api/` still proxied so
  non-browser clients are not hard-broken before the redirect.
- Port 443: TLS terminated with certificates mounted at `/etc/nginx/certs`
  (`fullchain.pem` / `privkey.pem`), SPA served via `try_files ... index.html`,
  `/api/` proxied to `http://api:8000`.
- Both `/api/` proxy blocks set `Host`, `X-Real-IP`, `X-Forwarded-For`, and
  `X-Forwarded-Proto $scheme`, matching Django's `SECURE_PROXY_SSL_HEADER` and
  `SECURE_SSL_REDIRECT` in `prod.py`.

## Notes / validation limits

Real TLS certificates cannot be generated or validated in this repository.
Threat-modeling note: the 443 block requires `fullchain.pem`/`privkey.pem` at
config-load time, so certificates MUST be provisioned (certbot/ACME volumes)
before the gateway is started. Syntax validation is done with throwaway
self-signed certificates locally; real handshake/pinning behavior must be
verified at the staging/deployment step.