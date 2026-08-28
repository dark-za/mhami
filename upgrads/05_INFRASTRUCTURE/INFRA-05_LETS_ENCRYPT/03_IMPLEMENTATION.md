# INFRA-05: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. The `bootstrap-cert` service must complete **before** `nginx` binds 443.

## Step 1: Add `certs` and `certbot-webroot` volumes

### 1.1 File before — `compose.yml`

```yaml
volumes:
  db-data:
  redis-data:
  media-data:
  static-data:
  certs:
  certbot-webroot:
```

### 1.2 Add to `compose.yml`

```yaml
volumes:
  db-data:
  redis-data:
  media-data:
  static-data:
  certs:
  certbot-webroot:
```

> Note: `certs` and `certbot-webroot` are added in INFRA-01 as placeholders. This step confirms they are present.

**Verify:**
```bash
Select-String -Path compose.yml -Pattern "^\s+certs:"
Select-String -Path compose.yml -Pattern "^\s+certbot-webroot:"
# Expected: 2 matches
```

---

## Step 2: Add `bootstrap-cert` and `certbot-renew` services

### 2.1 File before — `compose.yml`

```yaml
  certbot:
    image: certbot/certbot
    user: "1000:1000"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    pids_limit: 50
    mem_limit: 128m
    restart: "no"
    read_only: true
    tmpfs:
      - /tmp:size=32M,mode=1777
      - /var/lib/letsencrypt:size=32M,mode=0755,uid=1000,gid=1000
    volumes:
      - certs:/etc/letsencrypt:rw
      - certbot-webroot:/var/www/certbot:rw
    entrypoint: "/bin/sh"
    command: ["-c", "trap exit TERM; while :; do certbot renew; sleep 12h; done"]
```

### 2.2 File after

```yaml
  certbot:
    image: certbot/certbot
    user: "1000:1000"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    pids_limit: 50
    mem_limit: 128m
    restart: "no"
    read_only: true
    tmpfs:
      - /tmp:size=32M,mode=1777
      - /var/lib/letsencrypt:size=32M,mode=0755,uid=1000,gid=1000
    volumes:
      - certs:/etc/letsencrypt:rw
      - certbot-webroot:/var/www/certbot:rw
    entrypoint: "/bin/sh"
    command: ["-c", "trap exit TERM; while :; do certbot renew --post-hook 'nginx -t && kill -HUP 1'; sleep 12h; done"]

  bootstrap-cert:
    image: certbot/certbot
    user: "1000:1000"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    pids_limit: 50
    mem_limit: 128m
    restart: "no"
    read_only: true
    tmpfs:
      - /tmp:size=32M,mode=1777
    volumes:
      - certs:/etc/letsencrypt:rw
      - certbot-webroot:/var/www/certbot:rw
    entrypoint: "/bin/sh"
    command:
      - "-c"
      - |
        if [ -f /etc/letsencrypt/live/${LETSENCRYPT_DOMAIN}/fullchain.pem ]; then
          echo "Cert already exists; skipping bootstrap."
          exit 0
        fi
        if [ "$$LETSENCRYPT_STAGING" = "true" ]; then
          SERVER="--server https://acme-staging-v02.api.letsencrypt.org/directory"
        else
          SERVER=""
        fi
        certbot certonly --webroot --webroot-path=/var/www/certbot \
          $$SERVER \
          --email ${LETSENCRYPT_EMAIL} --agree-tos --no-eff-email \
          -d ${LETSENCRYPT_DOMAIN}

  certbot-renew:
    image: certbot/certbot
    user: "1000:1000"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    pids_limit: 50
    mem_limit: 128m
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp:size=32M,mode=1777
      - /var/lib/letsencrypt:size=32M,mode=0755,uid=1000,gid=1000
    volumes:
      - certs:/etc/letsencrypt:rw
      - certbot-webroot:/var/www/certbot:rw
    entrypoint: "/bin/sh"
    command:
      - "-c"
      - |
        trap exit TERM
        while :; do
          certbot renew --quiet --post-hook "nginx -t && kill -HUP 1" || echo "renew failed"
          sleep 12h
        done
```

### 2.3 `nginx` depends on `bootstrap-cert`

```yaml
  nginx:
    ...
    depends_on:
      api:
        condition: service_healthy
      frontend:
        condition: service_healthy
      bootstrap-cert:
        condition: service_completed_successfully
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml config --services | Sort-Object
# Expected: includes certbot, bootstrap-cert, certbot-renew
```

---

## Step 3: nginx config

### 3.1 New file: `infra/nginx/default.conf`

```nginx
# HTTP — only the ACME challenge is served; everything else redirects.
server {
  listen 8080;
  server_name ${LETSENCRYPT_DOMAIN};

  location /.well-known/acme-challenge/ {
    root /var/www/certbot;
  }

  location / {
    return 301 https://$host$request_uri;
  }
}

# HTTPS — SPA + API
server {
  listen 8443 ssl;
  server_name ${LETSENCRYPT_DOMAIN};

  ssl_certificate     /etc/nginx/certs/live/${LETSENCRYPT_DOMAIN}/fullchain.pem;
  ssl_certificate_key /etc/nginx/certs/live/${LETSENCRYPT_DOMAIN}/privkey.pem;
  ssl_protocols       TLSv1.2 TLSv1.3;
  ssl_ciphers         HIGH:!aNULL:!MD5;
  ssl_prefer_server_ciphers on;

  # SPA
  root /usr/share/nginx/html;
  index index.html;

  # API proxy
  location /api/ {
    proxy_pass http://api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
  }

  # SPA fallback
  location / {
    try_files $uri /index.html;
  }
}
```

### 3.2 Update `compose.yml` — `nginx` mounts

```yaml
  nginx:
    ...
    volumes:
      - ./infra/nginx:/etc/nginx/conf.d:ro
      - certs:/etc/nginx/certs:ro
      - certbot-webroot:/var/www/certbot:ro
    environment:
      LETSENCRYPT_DOMAIN: ${LETSENCRYPT_DOMAIN:?Set LETSENCRYPT_DOMAIN in .env}
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml exec nginx nginx -t
# Expected: "syntax is ok"
```

---

## Step 4: LE secrets

### 4.1 `compose.prod.yml`

```yaml
  nginx:
    environment:
      LETSENCRYPT_DOMAIN: ${LETSENCRYPT_DOMAIN:?Set LETSENCRYPT_DOMAIN in .env}

  certbot:
    environment:
      LETSENCRYPT_EMAIL: ${LETSENCRYPT_EMAIL:?Set LETSENCRYPT_EMAIL in .env}
      LETSENCRYPT_DOMAIN: ${LETSENCRYPT_DOMAIN:?Set LETSENCRYPT_DOMAIN in .env}
      LETSENCRYPT_STAGING: ${LETSENCRYPT_STAGING:-false}

  bootstrap-cert:
    environment:
      LETSENCRYPT_EMAIL: ${LETSENCRYPT_EMAIL:?Set LETSENCRYPT_EMAIL in .env}
      LETSENCRYPT_DOMAIN: ${LETSENCRYPT_DOMAIN:?Set LETSENCRYPT_DOMAIN in .env}
      LETSENCRYPT_STAGING: ${LETSENCRYPT_STAGING:-false}

  certbot-renew:
    environment:
      LETSENCRYPT_EMAIL: ${LETSENCRYPT_EMAIL:?Set LETSENCRYPT_EMAIL in .env}
      LETSENCRYPT_DOMAIN: ${LETSENCRYPT_DOMAIN:?Set LETSENCRYPT_DOMAIN in .env}
      LETSENCRYPT_STAGING: ${LETSENCRYPT_STAGING:-false}
```

**Verify:**
```bash
Select-String -Path compose.prod.yml -Pattern "LETSENCRYPT_"
# Expected: ≥3 matches
```

---

## Step 5: HTTPS smoke CI

### 5.1 New job in `.github/workflows/ci.yml`

```yaml
  https-smoke:
    runs-on: ubuntu-latest
    services:
      postgres: { ... }
      redis:    { ... }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Install backend
        run: pip install -r backend/requirements.txt
      - name: Migrate
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_smoke }
        run: cd backend && python manage.py migrate
      - name: Boot stack
        env:
          LETSENCRYPT_STAGING: "true"
          LETSENCRYPT_EMAIL: ci@example.com
          LETSENCRYPT_DOMAIN: ci.example.com
        run: |
          echo "127.0.0.1 ci.example.com" | sudo tee -a /etc/hosts
          docker compose -f compose.yml -f compose.prod.yml up -d
      - name: Wait for cert
        run: |
          for i in $(seq 1 60); do
            if curl -fsS --resolve ci.example.com:443:127.0.0.1 https://ci.example.com/api/health/live; then
              exit 0
            fi
            sleep 5
          done
          exit 1
      - name: HTTP redirect
        run: |
          curl -fsSI --resolve ci.example.com:80:127.0.0.1 http://ci.example.com/api/health/live | Select-String -Pattern "HTTP/1.1 301"
```

**Verify:**
```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "https-smoke"
# Expected: 1+ match
```

---

## Step 6: `CertExpiringSoon` alert

Append to `infra/monitoring/prometheus/alerts/business.yml`:

```yaml
- alert: CertExpiringSoon
  expr: mhami_cert_not_after_seconds - time() < 14 * 86400
  for: 1h
  labels: { severity: warning }
  annotations:
    summary: "Cert expires in {{ $value | humanizeDuration }}"
    runbook_url: "https://runbooks.example.com/cert-expiring"
```

> The `mhami_cert_not_after_seconds` metric is exposed by an exporter (e.g. `blackbox_exporter` with a `tcp_connect` probe + `ssl` module) or by a small Django management command. INFRA-04 can add a `celery-beat` job that exports the metric from `certs/live/<domain>/cert.pem`.

**Verify:**
```bash
Select-String -Path infra\monitoring\prometheus\alerts\business.yml -Pattern "CertExpiring"
# Expected: 1 match
```

---

## Step 7: Documentation

1. Update `docs/SERVER_INVENTORY.md` (domain, renewal schedule, cert path).
2. Update `docs/SECRET_MANAGEMENT.md` (LE secrets).
3. Update `docs/SECURITY_THREAT_MODEL.md` (HTTPS as A02 control).
4. Update `CHANGELOG.md` with an `INFRA-05` entry.
5. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Volumes | `grep -E '^\s+(certs|certbot-webroot):' compose.yml` | 2 matches |
| Services | `docker compose config --services \| grep -E 'certbot|bootstrap-cert|certbot-renew'` | 3 matches |
| `bootstrap-cert` exits 0 | `docker compose ps bootstrap-cert` | Exit 0 |
| Cert in volume | `docker compose exec nginx ls /etc/nginx/certs/live/<domain>/` | fullchain.pem, privkey.pem |
| nginx config | `docker compose exec nginx nginx -t` | syntax is ok |
| HTTP → HTTPS | `curl -fsSI http://<domain>/api/health/live` | 301 |
| HTTPS 200 | `curl -fsS https://<domain>/api/health/live` | 200 |
| Renewal dry-run | `certbot renew --dry-run` | "all simulated renewals succeeded" |
| HSTS | `curl -fsSI https://<domain>/ \| grep Strict-Transport-Security` | 1 match |
| `CertExpiringSoon` | `grep CertExpiring infra/monitoring/prometheus/alerts/business.yml` | 1 match |

---

## Rollback

```bash
git revert <infra05-commit-sha>
docker compose -f compose.yml -f compose.prod.yml down
docker volume rm mhami-backups_certs  # or whatever the volume is named
# Re-deploy without the LE services; the SPA will fall back to plain HTTP for dev.
```

> **Important:** the rollback does **not** invalidate the cert at LE. If the domain is moving away from this stack, also run `certbot revoke --cert-path /etc/letsencrypt/live/<domain>/cert.pem` on a machine that can reach the LE server.
