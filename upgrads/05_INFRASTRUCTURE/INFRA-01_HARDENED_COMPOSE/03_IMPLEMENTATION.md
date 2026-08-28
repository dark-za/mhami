# INFRA-01: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. The `x-backend-defaults` block is the single source of truth; if you change it in one file, change it in the other (or fail the CI check).

## Step 1: Sync the `x-backend-defaults` anchor

### 1.1 Source of truth: `compose.yml`

```yaml
# compose.yml
x-backend-defaults: &backend_defaults
  build:
    context: ./backend
  user: "1000:1000"
  cap_drop:
    - ALL
  cap_add:
    - NET_BIND_SERVICE
  security_opt:
    - no-new-privileges:true
  pids_limit: 100
  mem_limit: 512m
  cpus: 1.0
  restart: unless-stopped
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:8000/api/health/live"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 30s
```

### 1.2 Make `compose.prod.yml` identical

```yaml
# compose.prod.yml
x-backend-defaults: &backend_defaults
  build:
    context: ./backend
  user: "1000:1000"
  cap_drop:
    - ALL
  cap_add:
    - NET_BIND_SERVICE
  security_opt:
    - no-new-privileges:true
  pids_limit: 100
  mem_limit: 512m
  cpus: 1.0
  restart: unless-stopped
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:8000/api/health/live"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 30s
```

### 1.3 CI check: `scripts/ci/check_compose_anchor.sh`

```bash
#!/usr/bin/env bash
# Fail if x-backend-defaults drifts between compose.yml and compose.prod.yml.

set -euo pipefail

yml=$(awk '/^x-backend-defaults: &backend_defaults/{flag=1; next} flag && /^[a-zA-Z]/{flag=0} flag' compose.yml)
prod=$(awk '/^x-backend-defaults: &backend_defaults/{flag=1; next} flag && /^[a-zA-Z]/{flag=0} flag' compose.prod.yml)

if [ "$yml" != "$prod" ]; then
  echo "::error::x-backend-defaults drift between compose.yml and compose.prod.yml"
  diff <(echo "$yml") <(echo "$prod")
  exit 1
fi
```

Add to `.github/workflows/ci.yml`:

```yaml
  compose-anchor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check anchor parity
        run: bash scripts/ci/check_compose_anchor.sh
```

**Verify:**
```bash
bash scripts/ci/check_compose_anchor.sh
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## Step 2: Promote `DJANGO_DEBUG: "false"` in `compose.prod.yml`

### 2.1 Before

```yaml
x-backend-prod-env: &backend_prod_env
  DJANGO_SETTINGS_MODULE: config.settings.prod
  DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
  # ...
```

### 2.2 After

```yaml
x-backend-prod-env: &backend_prod_env
  DJANGO_SETTINGS_MODULE: config.settings.prod
  DJANGO_DEBUG: "false"
  DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
  # ...
```

**Verify:**
```bash
Select-String -Path compose.prod.yml -Pattern "DJANGO_DEBUG: \"false\""
# Expected: 1 match
```

---

## Step 3: Add `read_only` + `tmpfs` to `worker` and `beat`

### 3.1 Before — `compose.prod.yml`

```yaml
  worker:
    <<: *backend_defaults
    command: [ ... ]
```

### 3.2 After

```yaml
  worker:
    <<: *backend_defaults
    read_only: true
    tmpfs:
      - /tmp:size=50M,mode=1777
    command: [ ... ]

  beat:
    <<: *backend_defaults
    read_only: true
    tmpfs:
      - /tmp:size=32M,mode=1777
    command: [ ... ]
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml config | Select-String -Pattern "read_only: true"
# Expected: matches for api, worker, beat, db, redis, frontend, nginx
```

---

## Step 4: Add `frontend` and `nginx` services to `compose.yml`

### 4.1 `frontend`

```yaml
  frontend:
    build:
      context: ./frontend
    user: "1000:1000"
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    pids_limit: 100
    mem_limit: 256m
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp:size=32M,mode=1777
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:80/ | grep -q '<title>'"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    ports:
      - "3000:80"
    depends_on:
      api:
        condition: service_healthy
```

### 4.2 `nginx`

```yaml
  nginx:
    image: nginx:1.27
    user: "1000:1000"
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    pids_limit: 100
    mem_limit: 128m
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp:size=16M,mode=1777
      - /var/cache/nginx:size=32M,mode=0755,uid=1000,gid=1000
      - /var/run:size=8M,mode=0755,uid=1000,gid=1000
    volumes:
      - ./infra/nginx:/etc/nginx/conf.d:ro
      - certs:/etc/nginx/certs:ro
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
    ports:
      - "80:8080"
      - "443:8443"
    depends_on:
      api:
        condition: service_healthy
      frontend:
        condition: service_healthy
```

**Verify:**
```bash
docker compose -f compose.yml config --services | Sort-Object
# Expected: api, beat, certbot, db, frontend, nginx, redis, worker
```

---

## Step 5: Add a `certbot` placeholder service (INFRA-05 fills it in)

```yaml
  certbot:
    image: certbot/certbot
    user: "1000:1000"
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
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

**Verify:**
```bash
Select-String -Path compose.yml -Pattern "certbot"
# Expected: 1+ match
```

---

## Step 6: Healthcheck on `worker`, `beat`, `db`, `redis`, `frontend`, `nginx`

`worker`:
```yaml
    healthcheck:
      test: ["CMD-SHELL", "celery -A config.celery inspect ping -d celery@$$HOSTNAME || exit 1"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 60s
```

`beat`:
```yaml
    healthcheck:
      test: ["CMD-SHELL", "pgrep -f 'celery.*beat' || exit 1"]
      interval: 60s
      timeout: 5s
      retries: 5
      start_period: 60s
```

`db` (already present) and `redis` (already present) — confirm:
```bash
Select-String -Path compose.yml -Pattern "pg_isready"
Select-String -Path compose.yml -Pattern "redis-cli ping"
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml config | Select-String -Pattern "healthcheck"
# Expected: 7+ matches (one per service)
```

---

## Step 7: Resource bounds on every service

Confirm every service has `mem_limit` and `pids_limit`:

```bash
docker compose -f compose.yml -f compose.prod.yml config | Select-String -Pattern "mem_limit:"
# Expected: 8 matches
```

---

## Step 8: Verify

```bash
# 1. Static check
docker compose -f compose.yml -f compose.prod.yml config 2>&1 | Out-String | Select-Object -First 30
echo "Exit code: $LASTEXITCODE"
# Expected: 0

# 2. Runtime check
docker compose -f compose.yml -f compose.prod.yml up -d
docker compose -f compose.yml -f compose.prod.yml ps
# Expected: all Up (healthy) within 60s

# 3. Non-root inside api
docker compose -f compose.yml -f compose.prod.yml exec api id
# Expected: uid=1000(user) gid=1000(user) groups=1000(user)

# 4. cap_drop
docker compose -f compose.yml -f compose.prod.yml exec api capsh --print | Select-String "Bounding"
# Expected: only cap_net_bind_service left
```

---

## Step 9: Documentation

1. Update `docs/SECRET_MANAGEMENT.md` with the full list of mandatory secrets.
2. Update `CHANGELOG.md` with an `INFRA-01` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| `docker compose config` clean | `docker compose -f compose.yml -f compose.prod.yml config` | exit 0 |
| All services healthy | `docker compose -f compose.yml -f compose.prod.yml ps` | all Up (healthy) |
| `api` runs as non-root | `docker compose exec api id` | uid=1000 |
| `api` caps restricted | `docker compose exec api capsh --print` | only NET_BIND_SERVICE |
| Mandatory secrets fail-fast | `Select-String compose.prod.yml -Pattern "\${[A-Z_]+:\?"` | ≥7 matches |
| Anchor parity | `bash scripts/ci/check_compose_anchor.sh` | exit 0 |

---

## Rollback

```bash
git revert <infra01-commit-sha>
docker compose -f compose.yml -f compose.prod.yml up -d
docker compose -f compose.yml -f compose.prod.yml ps
# Expected: services back to the previous posture
```
