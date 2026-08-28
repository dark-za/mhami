# INFRA-05: Test Strategy

> **Rule:** every check in this file must run against a real `docker compose up`. The **HTTPS smoke test in CI is the gate** for production.

## 1. Unit Tests

Not applicable.

## 2. Integration Tests

### 2.1 `nginx -t`

```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx nginx -t
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### 2.2 `certbot renew --dry-run`

```bash
docker compose -f compose.yml -f compose.prod.yml exec certbot-renew certbot renew --dry-run
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### 2.3 `certbot certificates`

```bash
docker compose -f compose.yml -f compose.prod.yml exec certbot certbot certificates
# Expected: at least one VALID cert with > 60 days remaining
```

---

## 3. End-to-End Tests

### 3.1 `bootstrap-cert` exit code

```bash
docker compose -f compose.yml -f compose.prod.yml ps bootstrap-cert
# Expected: "Exit 0"
```

### 3.2 Cert in volume

```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx ls /etc/nginx/certs/live/<domain>/
# Expected: fullchain.pem, privkey.pem, chain.pem
```

### 3.3 HTTP → HTTPS redirect

```bash
curl -fsSI --resolve <domain>:80:127.0.0.1 http://<domain>/api/health/live | Select-String -Pattern "HTTP/1.1 301"
curl -fsSI --resolve <domain>:80:127.0.0.1 http://<domain>/api/health/live | Select-String -Pattern "Location: https://"
# Expected: 2 matches
```

### 3.4 HTTPS works

```bash
curl -fsS --resolve <domain>:443:127.0.0.1 https://<domain>/api/health/live
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### 3.5 HSTS header

```bash
curl -fsSI --resolve <domain>:443:127.0.0.1 https://<domain>/ | Select-String -Pattern "Strict-Transport-Security"
# Expected: 1 match
```

### 3.6 ACME challenge

```bash
# Create a token in the webroot
docker compose -f compose.yml -f compose.prod.yml exec certbot sh -c 'mkdir -p /var/www/certbot/.well-known/acme-challenge && echo test > /var/www/certbot/.well-known/acme-challenge/test'
curl -fsS --resolve <domain>:80:127.0.0.1 http://<domain>/.well-known/acme-challenge/test
# Expected: "test"
```

### 3.7 CI `https-smoke`

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "https-smoke"
# Expected: 1+ match
```

### 3.8 `CertExpiringSoon` alert

```bash
Select-String -Path infra\monitoring\prometheus\alerts\business.yml -Pattern "CertExpiring"
# Expected: 1 match
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| `nginx -t` | 1 | exit 0 |
| `certbot renew --dry-run` | 1 | exit 0 |
| `certbot certificates` | 1 | ≥1 cert, > 60 days |
| `bootstrap-cert` exit | 1 | 0 |
| Cert in volume | 3 | fullchain, privkey, chain |
| HTTP → HTTPS redirect | 1 | 301 + Location |
| HTTPS works | 1 | 200 |
| HSTS | 1 | header present |
| ACME challenge | 1 | 200 |
| `https-smoke` CI | 1 | present |
| `CertExpiringSoon` | 1 | present |

---

## 5. Run Tests

### 5.1 Local (with a delegated domain)

```bash
# 1. Set the secrets
export LETSENCRYPT_DOMAIN=staging.example.com
export LETSENCRYPT_EMAIL=admin@example.com
export LETSENCRYPT_STAGING=true  # avoid rate limits in dev

# 2. Boot
docker compose -f compose.yml -f compose.prod.yml up -d

# 3. Wait for bootstrap-cert
for i in $(seq 1 60); do
  if docker compose ps bootstrap-cert | Select-String -Pattern "Exit 0"; then break; fi
  sleep 5
done

# 4. Verify
curl -fsSI --resolve $LETSENCRYPT_DOMAIN:80:127.0.0.1 http://$LETSENCRYPT_DOMAIN/api/health/live
curl -fsS  --resolve $LETSENCRYPT_DOMAIN:443:127.0.0.1 https://$LETSENCRYPT_DOMAIN/api/health/live
```

### 5.2 Local (with a non-delegated domain — fake webroot)

```bash
# Set LETSENCRYPT_DOMAIN to a hostname that resolves to 127.0.0.1 in /etc/hosts.
echo "127.0.0.1 ci.example.com" | sudo tee -a /etc/hosts
export LETSENCRYPT_DOMAIN=ci.example.com
export LETSENCRYPT_EMAIL=ci@example.com
export LETSENCRYPT_STAGING=true

docker compose -f compose.yml -f compose.prod.yml up -d
# Same verifications as above.
```

### 5.3 CI

The `https-smoke` job runs against the LE `staging` server.

### 5.4 Failure simulation

| Scenario | Expected |
|---|---|
| Remove the `bootstrap-cert` `depends_on` | `nginx` starts before the cert exists; `nginx -t` fails |
| Remove the 301 redirect | `curl -fsSI http://<domain>/` returns 200 instead of 301 |
| Set `LETSENCRYPT_STAGING=false` in CI | rate-limit errors; CI fails |
| Set `LETSENCRYPT_EMAIL` to empty | compose fails (mandatory secret) |

---

## 6. Cross-links

- [INFRA-01 — Hardened Compose](..) — `certbot` placeholder; volumes added there.
- [INFRA-02 — CSP](..) — `Strict-Transport-Security` is in the same config.
- [INFRA-04 — Prometheus/Grafana](..) — `CertExpiringSoon` alert.
- [QA-05 — OWASP ZAP](..) — ZAP runs against the HTTPS endpoint.
