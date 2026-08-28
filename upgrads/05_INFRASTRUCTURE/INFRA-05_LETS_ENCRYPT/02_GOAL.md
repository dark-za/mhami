# INFRA-05: Goal and Plan

## SMART Goal

> Within **3 days**, deploy **certbot** as a Compose service that
> bootstraps a Let's Encrypt certificate via HTTP-01, mounts it on
> `nginx`, runs `certbot renew` every 12 hours, redirects all HTTP
> traffic (including `/api/`) to HTTPS, and verifies the end-to-end
> HTTPS path in CI against the LE `staging` server.

## Detailed Acceptance Standards

### Standard 1: Service matrix

| Service | Profile | Restart | Purpose |
|---|---|---|---|
| `certbot` | main | `no` | long-running shell that renews every 12h |
| `bootstrap-cert` | main | `no` | one-shot `certonly --webroot`; `nginx` depends on it |
| `certbot-renew` | main | `unless-stopped` | wrapped loop with `--post-hook "nginx -s reload"` |

### Standard 2: nginx blocks

```nginx
server {
  listen 8080;  # mapped to host :80
  server_name <domain>;

  location /.well-known/acme-challenge/ {
    root /var/www/certbot;
  }

  location / {
    return 301 https://$host$request_uri;
  }
}

server {
  listen 8443 ssl;  # mapped to host :443
  server_name <domain>;

  ssl_certificate     /etc/nginx/certs/live/<domain>/fullchain.pem;
  ssl_certificate_key /etc/nginx/certs/live/<domain>/privkey.pem;

  # ... rest of the SPA + API proxy
}
```

### Standard 3: HTTP → HTTPS redirect

| Path | Status | Location |
|---|---|---|
| `/.well-known/acme-challenge/*` | 200 | (served by webroot) |
| Everything else (including `/api/`) | 301 | `https://<host><uri>` |

### Standard 4: Renewal

```bash
# certbot-renew entrypoint
trap exit TERM
while :; do
  certbot renew --quiet --post-hook "nginx -t && nginx -s reload"
  sleep 12h
done
```

### Standard 5: Bootstrap order

```yaml
services:
  nginx:
    depends_on:
      bootstrap-cert:
        condition: service_completed_successfully
```

The `bootstrap-cert` service runs **once** and exits 0; `nginx` starts only after the cert is in the volume.

### Standard 6: CI smoke (LE staging)

```yaml
  https-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Boot stack with --staging
        env:
          LETSENCRYPT_STAGING: "true"
          LETSENCRYPT_EMAIL: ci@example.com
          LETSENCRYPT_DOMAIN: ci.example.com
        run: |
          docker compose -f compose.yml -f compose.prod.yml up -d
          sleep 60
          curl -fsS https://ci.example.com/api/health/live
```

### Standard 7: Alert (cross-link INFRA-04)

`infra/monitoring/prometheus/alerts/business.yml` adds:

```yaml
- alert: CertExpiringSoon
  expr: mhami_cert_not_after_seconds - time() < 14 * 86400
  for: 1h
  labels: { severity: warning }
  annotations:
    summary: "Cert expires in {{ $value | humanizeDuration }}"
    runbook_url: "https://runbooks.example.com/cert-expiring"
```

### Standard 8: Secrets

| Name | Purpose | Storage |
|---|---|---|
| `LETSENCRYPT_EMAIL` | registration | CI / compose |
| `LETSENCRYPT_DOMAIN` | the FQDN to certify | CI / compose |
| `LETSENCRYPT_STAGING` | `true` / `false` | CI / compose |

---

## Detailed Implementation Plan

### Day 1 — Volumes + services

- [ ] Add `certs` and `certbot-webroot` volumes to `compose.yml`.
- [ ] Add `bootstrap-cert` one-shot service.
- [ ] Add `certbot-renew` long-running service.
- [ ] Wire `LETSENCRYPT_*` env vars (fail-fast).

### Day 2 — nginx + redirect

- [ ] Add the `server` block for `:80` with `/.well-known/acme-challenge/` and the 301 redirect.
- [ ] Add the `server` block for `:443` with `ssl_certificate` / `ssl_certificate_key`.
- [ ] Mount `certs:/etc/nginx/certs:ro` and `certbot-webroot:/var/www/certbot:ro` on `nginx`.
- [ ] `nginx` depends on `bootstrap-cert: service_completed_successfully`.

### Day 3 — CI + alert + docs

- [ ] Add `https-smoke` CI job against LE staging.
- [ ] Add `CertExpiringSoon` alert in `business.yml`.
- [ ] Update `docs/SERVER_INVENTORY.md` (domain, renewal schedule).
- [ ] Update `docs/SECRET_MANAGEMENT.md` (LE secrets).
- [ ] Update `CHANGELOG.md`.

---

## Dependency Graph

```
volumes (Day 1)
    ↓
bootstrap-cert + certbot-renew (Day 1)
    ↓
nginx :80/:443 + redirect (Day 2)
    ↓
https-smoke CI (Day 3)
    ↓
CertExpiringSoon alert (Day 3)
    ↓
docs + sign-off
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | `bootstrap-cert` exits 0 | DevOps |
| CP-2 | Cert in volume | DevOps |
| CP-3 | HTTP → HTTPS redirect | DevOps |
| CP-4 | HTTPS smoke 200 | DevOps |
| CP-5 | `certbot renew --dry-run` green | DevOps |
| CP-6 | `https-smoke` CI green | DevOps |
| CP-7 | `CertExpiringSoon` alert in place | DevOps |
| CP-8 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If the LE staging server rate-limits the CI runner → add `LETSENCRYPT_STAGING=true` for non-prod; do not lower the rate.
- If the renewal hook fails to reload nginx → investigate the post-hook; do not silence the alert.
- If the domain is not delegated yet → block the deployment; do not ship an unverified cert.
