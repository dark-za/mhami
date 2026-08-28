# INFRA-05: Verification Commands

> **Instructions:** Run baseline (Phase 1) before the change, then post-fix (Phase 2) to confirm the cert is bootstrapped, the redirect works, the renewal is scheduled, and the HTTPS smoke test is green.

## Phase 1: Pre-Fix Proof

### Command 1.1 — No certbot

```bash
Get-ChildItem -Recurse -Filter "certbot*" -ErrorAction SilentlyContinue
# Expected: 0 matches
```

### Command 1.2 — No `certs` volume

```bash
Select-String -Path compose.yml -Pattern "certs:"
# Expected: 0 matches
```

### Command 1.3 — No `ssl_certificate` in nginx

```bash
Select-String -Path infra\nginx\security-headers.conf -Pattern "ssl_certificate"
# Expected: 0 matches
```

### Command 1.4 — No `LETSENCRYPT_EMAIL` documented

```bash
Select-String -Path docs\SECRET_MANAGEMENT.md -Pattern "LETSENCRYPT_EMAIL"
# Expected: 0 matches
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — `certs` and `certbot-webroot` volumes

```bash
Select-String -Path compose.yml -Pattern "certs:"
Select-String -Path compose.yml -Pattern "certbot-webroot:"
# Expected: 2 matches
```

### Command 2.2 — `certbot`, `bootstrap-cert`, `certbot-renew` services

```bash
docker compose -f compose.yml -f compose.prod.yml config --services | Sort-Object
# Expected: includes certbot, bootstrap-cert, certbot-renew
```

### Command 2.3 — `bootstrap-cert` succeeded

```bash
docker compose -f compose.yml -f compose.prod.yml ps bootstrap-cert
# Expected: "Exit 0" or "completed successfully"
```

### Command 2.4 — Certificate exists in the volume

```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx ls /etc/nginx/certs/live/<domain>/
# Expected: fullchain.pem, privkey.pem, chain.pem
```

### Command 2.5 — nginx has the cert

```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx grep ssl_certificate /etc/nginx/conf.d/default.conf
# Expected: 2 matches (fullchain.pem, privkey.pem)
```

### Command 2.6 — HTTP → HTTPS redirect

```bash
curl -fsSI http://<domain>/api/health/live | Select-String -Pattern "HTTP/1.1 301"
curl -fsSI http://<domain>/api/health/live | Select-String -Pattern "Location: https://"
# Expected: 2 matches
```

### Command 2.7 — HTTPS works

```bash
curl -fsS https://<domain>/api/health/live
echo "Exit code: $LASTEXITCODE"
# Expected: 0, body "ok"
```

### Command 2.8 — Renewal runs

```bash
docker compose -f compose.yml -f compose.prod.yml exec certbot-renew certbot renew --dry-run
echo "Exit code: $LASTEXITCODE"
# Expected: 0 ("Congratulations, all simulated renewals succeeded")
```

### Command 2.9 — Cert is valid for > 60 days

```bash
docker compose -f compose.yml -f compose.prod.yml exec certbot certbot certificates | Select-String -Pattern "VALID"
# Expected: 1 match, "VALID: 89 days"
```

### Command 2.10 — HSTS is emitted

```bash
curl -fsSI https://<domain>/ | Select-String -Pattern "Strict-Transport-Security"
# Expected: 1 match
```

---

## Phase 3: Regression / Safety

### Command 3.1 — nginx config valid

```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx nginx -t
# Expected: "syntax is ok"
```

### Command 3.2 — Existing services still boot

```bash
docker compose -f compose.yml -f compose.prod.yml ps
# Expected: all Up (healthy) or Exit 0 for one-shots
```

### Command 3.3 — `https-smoke` CI job

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "https-smoke"
# Expected: 1+ match
```

### Command 3.4 — `CertExpiringSoon` alert

```bash
Select-String -Path infra\monitoring\prometheus\alerts\business.yml -Pattern "CertExpiring"
# Expected: 1 match (added by cross-link from INFRA-04)
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 / 1.4 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 / 2.6 / 2.7 / 2.8 / 2.9 / 2.10 green
- ✅ Command 3.1 / 3.2 / 3.3 / 3.4 no regression
