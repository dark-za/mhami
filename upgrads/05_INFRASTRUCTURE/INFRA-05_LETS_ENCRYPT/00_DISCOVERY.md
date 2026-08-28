# INFRA-05: Let's Encrypt (certbot) for production HTTPS

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The platform runs behind `nginx` (introduced in INFRA-01), but no service **provisions or renews a TLS certificate**. There is no `certbot` service, no `webroot` volume, and no DNS / HTTP-01 challenge configured. The `Strict-Transport-Security` header is in `security-headers.conf`, but it points at a certificate that does not exist. Gate-B requires HTTPS with a real, automatically-renewed certificate.

**Evidence gathered:**
- `compose.yml` — no `certbot` service (added as a placeholder in INFRA-01, but not wired in).
- `compose.prod.yml` — no `certs` volume mount on `nginx`.
- `infra/nginx/security-headers.conf` — `Strict-Transport-Security` is set, but no `ssl_certificate` is referenced in any `server` block.
- `docs/SERVER_INVENTORY.md` — does not list a domain or a renewal schedule.
- `docs/SECRET_MANAGEMENT.md` — does not list `LETSENCRYPT_EMAIL`.

### Impact

| Dimension | Impact |
|---|---|
| Functional | No HTTPS; users hit a 525/526 from Cloudflare or a 497 from nginx. |
| Security | `Strict-Transport-Security` is meaningless without a real cert. |
| Compliance | Gate-B requires HTTPS for the API and SPA. |
| Operational | Manual renewal is error-prone and forgotten. |

### Reproducible Evidence

```bash
# 1. Confirm no certbot
Test-Path scripts\ci\check_https.sh
# Expected today: False

Get-ChildItem -Recurse -Filter "certbot*" -ErrorAction SilentlyContinue
# Expected today: 0 matches

# 2. Confirm no certs volume
Select-String -Path compose.yml -Pattern "certs:"
# Expected today: 0 matches (placeholder added by INFRA-01 still pending)

# 3. Confirm HSTS but no ssl_certificate
Select-String -Path infra\nginx\security-headers.conf -Pattern "ssl_certificate"
# Expected today: 0 matches
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `certbot` service | none | running with webroot plugin |
| `certs` volume | none | mounted on `nginx` and `certbot` |
| HTTP-01 challenge | none | `/var/www/certbot` webroot |
| `ssl_certificate` in nginx | none | pointing at `/etc/nginx/certs/live/<domain>/fullchain.pem` |
| HTTP → HTTPS redirect | none | all paths including `/api/` |
| Renewal cron | none | `certbot renew` every 12h, with `--reload` on success |
| Bootstrap before nginx binds 443 | n/a | nginx waits for the cert to exist (compose `depends_on: service_completed_successfully`) |
| HTTPS smoke test in CI | none | `curl -fsS https://staging.example.com/api/health/live` |
| Staging environment (LE `staging` server) | none | `--staging` flag in CI, real LE in prod |

---

## 3. Goal Statement

> Within **3 days**, deploy **certbot** as a Compose service that bootstraps a Let's Encrypt certificate via HTTP-01, mounts it on `nginx`, runs `certbot renew` every 12 hours, redirects all HTTP traffic (including `/api/`) to HTTPS, and verifies the end-to-end HTTPS path in CI against the LE `staging` server.

### Acceptance Criteria

1. **AC-1:** `certbot` service is in `compose.yml` and `compose.prod.yml` with the `webroot` plugin and the `certs` and `certbot-webroot` volumes.
2. **AC-2:** A `bootstrap-cert` one-shot service runs `certbot certonly --webroot ... -d <domain>` and `nginx` waits for it (`service_completed_successfully`).
3. **AC-3:** `nginx` has two `server` blocks: one on `:80` with a `location /.well-known/acme-challenge/` and a `301` redirect to `:443` for everything else; one on `:443` with `ssl_certificate` / `ssl_certificate_key` pointing at the certbot volume.
4. **AC-4:** A `certbot-renew` service runs `certbot renew --quiet --post-hook "nginx -s reload"` in a loop with `sleep 12h`.
5. **AC-5:** The renewal cert is renewed at `< 30 days remaining`.
6. **AC-6:** `curl -fsS http://<domain>/api/health/live` returns `301` to `https://<domain>/api/health/live`.
7. **AC-7:** `curl -fsS https://<domain>/api/health/live` returns `200`.
8. **AC-8:** A CI job `https-smoke` runs against the LE `staging` server and exits 0.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LE rate limits during dev | High | High | Use `--staging` server in non-prod; document in `docs/SECRET_MANAGEMENT.md`. |
| Renewal fails silently | Medium | High | `certbot renew --post-hook "nginx -s reload"`; alert on `BackupLastRunOld` style metric for cert expiry. |
| `nginx -s reload` after a renewed cert fails | Medium | High | `nginx -t` before `reload`; the `certbot-renew` service uses a wrapper script. |
| Bootstrap order — nginx binds 443 before the cert exists | High | High | `nginx` depends on `bootstrap-cert: service_completed_successfully`. |
| `webroot` path not exposed | Medium | Medium | Add `location /.well-known/acme-challenge/` to the `:80` server. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `certs` and `certbot-webroot` named volumes to `compose.yml` | DevOps | not-started |
| 2 | Add `certbot` service placeholder (already in INFRA-01) | DevOps | not-started |
| 3 | Add `bootstrap-cert` one-shot service | DevOps | not-started |
| 4 | Add `certbot-renew` long-running service | DevOps | not-started |
| 5 | Configure `nginx` to mount `certs` and use the `webroot` | DevOps | not-started |
| 6 | Add HTTP → HTTPS redirect including `/api/` | DevOps | not-started |
| 7 | Wire `LETSENCRYPT_EMAIL` and `LETSENCRYPT_DOMAIN` secrets | DevOps | not-started |
| 8 | Add `https-smoke` CI job (LE staging) | DevOps | not-started |
| 9 | Add `CertExpiringSoon` alert (cross-link INFRA-04) | DevOps | not-started |
| 10 | Update `docs/SECURITY_THREAT_MODEL.md` and `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [infra/nginx/security-headers.conf](../../../infra/nginx/security-headers.conf)
- [compose.yml](../../../compose.yml)
- [compose.prod.yml](../../../compose.prod.yml)
- [docs/SECRET_MANAGEMENT.md](../../../docs/SECRET_MANAGEMENT.md)
- [INFRA-01 — Hardened Compose](..) — `certbot` placeholder added there
- [INFRA-04 — Prometheus/Grafana](..) — `CertExpiringSoon` alert
