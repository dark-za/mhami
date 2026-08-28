# Cloudflare Assets

Edge and Tunnel configuration guidance for the platform.

Phase 13 requires production to be reached behind Cloudflare Tunnel in front of
the gateway published by `../compose.prod.yml` (NGINX on 443/80). TLS is
terminated at NGINX with certificates mounted at `/etc/nginx/certs`.

Secrets and tokens must never be stored in this repository (`../docs/SECRET_MANAGEMENT.md`).

## Validation limits

No Tunnel credentials or edge configuration exist in this repository, and none
can be provisioned here. Tunnel routing smoke tests must be run at deployment
time.