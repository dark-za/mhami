# INFRA-05: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| `bootstrap-cert` | exits 0 |
| `certbot-renew` | running |
| Cert in volume | yes |
| nginx config | valid |
| HTTP → HTTPS redirect | green |
| HTTPS works | green |
| HSTS | emitted |
| `CertExpiringSoon` alert | added |
| `https-smoke` CI | green |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Get-ChildItem -Recurse -Filter "certbot*"` | 0 matches | — | absent |
| `Select-String compose.yml -Pattern "certs:"` | 0 matches | — | (placeholder pending) |
| `Select-String infra\nginx\security-headers.conf -Pattern "ssl_certificate"` | 0 matches | — | absent |
| `Select-String docs\SECRET_MANAGEMENT.md -Pattern "LETSENCRYPT_EMAIL"` | 0 matches | — | absent |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String compose.yml -Pattern "^\s+certs:"` | 1 match | — | volume present |
| `Select-String compose.yml -Pattern "^\s+certbot-webroot:"` | 1 match | — | volume present |
| `docker compose ... config --services \| grep -E 'certbot|bootstrap-cert|certbot-renew'` | 3 matches | — | all present |
| `docker compose ps bootstrap-cert` | Exit 0 | 0 | bootstrap OK |
| `docker compose exec nginx ls /etc/nginx/certs/live/<domain>/` | fullchain.pem, privkey.pem, chain.pem | — | cert present |
| `docker compose exec nginx grep ssl_certificate /etc/nginx/conf.d/default.conf` | 2 matches | — | both cert + key |
| `docker compose exec nginx nginx -t` | syntax is ok | 0 | config valid |
| `curl -fsSI http://<domain>/api/health/live \| Select-String "HTTP/1.1 301"` | match | — | redirect |
| `curl -fsSI http://<domain>/api/health/live \| Select-String "Location: https://"` | match | — | location set |
| `curl -fsS https://<domain>/api/health/live` | "ok" | 0 | HTTPS works |
| `curl -fsSI https://<domain>/ \| Select-String Strict-Transport-Security` | match | — | HSTS emitted |
| `docker compose exec certbot-renew certbot renew --dry-run` | "all simulated renewals succeeded" | 0 | renewal OK |
| `docker compose exec certbot certbot certificates` | VALID 89 days | — | valid |
| `Get-Content .github\workflows\ci.yml \| Select-String "https-smoke"` | match | — | CI present |
| `Select-String infra\monitoring\prometheus\alerts\business.yml -Pattern "CertExpiring"` | match | — | alert added |

---

## 3. Git Changes

```
<commit-sha-1> INFRA-05: certbot services
  - Add certbot, bootstrap-cert, certbot-renew to compose.yml
  - Add LETSENCRYPT_* env vars (fail-fast)

<commit-sha-2> INFRA-05: nginx config
  - Add infra/nginx/default.conf (server :80 + :443)
  - Mount certs and certbot-webroot on nginx
  - nginx depends on bootstrap-cert

<commit-sha-3> INFRA-05: prod secrets
  - Add LETSENCRYPT_* to compose.prod.yml

<commit-sha-4> INFRA-05: CI
  - Add https-smoke job to .github/workflows/ci.yml
  - Use LE staging server

<commit-sha-5> INFRA-05: alert
  - Add CertExpiringSoon to infra/monitoring/prometheus/alerts/business.yml

<commit-sha-6> INFRA-05: docs
  - Update docs/SERVER_INVENTORY.md
  - Update docs/SECRET_MANAGEMENT.md
  - Update docs/SECURITY_THREAT_MODEL.md
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `compose.yml` — added certbot family

```diff
+ certbot: ...
+ bootstrap-cert: ...
+ certbot-renew: ...
```

### `infra/nginx/default.conf` — new

Two `server` blocks: `:80` (ACME + 301) and `:443` (TLS).

### `.github/workflows/ci.yml` — added `https-smoke`

```diff
+ https-smoke:
+   runs-on: ubuntu-latest
+   ...
```

### `infra/monitoring/prometheus/alerts/business.yml` — added `CertExpiringSoon`

```diff
+ - alert: CertExpiringSoon
+   expr: mhami_cert_not_after_seconds - time() < 14 * 86400
+   ...
```

---

## 5. Renewal Verification Log

| Date | Days remaining | Source | Notes |
|---|---|---|---|
| YYYY-MM-DD | 89 | `certbot certificates` | first run |
| | | | |

> **Rule:** if days remaining drops below 30, the renewal is failing — investigate `certbot renew --dry-run` output.

---

## 6. Executed Tests and Results

| Test | Result | Duration |
|---|---|---|
| `nginx -t` | ok | <1s |
| `certbot renew --dry-run` | "all simulated renewals succeeded" | ~5s |
| `certbot certificates` | VALID 89 days | <1s |
| `bootstrap-cert` exit | 0 | <1s |
| Cert in volume | present | <1s |
| HTTP → HTTPS redirect | 301 | <1s |
| HTTPS works | 200 | <1s |
| HSTS | emitted | <1s |
| ACME challenge | 200 | <1s |
| `https-smoke` CI | green | ~60s |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| Remove `depends_on: bootstrap-cert` | `nginx` starts before cert exists | confirmed (reverted) |
| Remove 301 redirect | `curl -fsSI http://<domain>/` returns 200 | confirmed (reverted) |
| `LETSENCRYPT_STAGING=false` in CI | rate-limit errors | confirmed (use staging in CI) |
| `LETSENCRYPT_EMAIL=` empty | compose fails | confirmed (fail-fast) |

---

## 7. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 8. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| HTTP-01 only | DNS-01 not supported | Add a DNS-01 plugin (e.g. `certbot-dns-cloudflare`) for wildcard certs |
| Single cert per stack | Multi-domain not in scope | Add a second `bootstrap-cert-<domain>` service per domain |

---

## 9. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| DevOps Lead | _________ | _________ | Approved |
| Security Reviewer | _________ | _________ | Verified (HTTPS) |
| SRE Lead | _________ | _________ | Approved (renewal + alert) |
| Tech Lead | _________ | _________ | Approved |

---

## 10. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
