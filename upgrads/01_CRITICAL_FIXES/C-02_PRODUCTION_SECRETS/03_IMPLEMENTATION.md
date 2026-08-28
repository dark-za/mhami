# C-02: Implementation Guide

> This guide covers environment propagation only. It does not prove that the
> production topology builds, starts, serves TLS, or restores data; those are
> Gate B requirements and must be verified separately.

## Step 1: Update `compose.yml`

**Location:** `compose.yml:31-37`

```yaml
api:
  build:
    context: ./backend
  environment:
    DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-config.settings.dev}
    DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
    DJANGO_DEBUG: ${DJANGO_DEBUG:-true}
    DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,api}
    MFA_ENCRYPTION_KEYS: ${MFA_ENCRYPTION_KEYS:-}
    # ✅ Newly added
    AUDIT_HMAC_SECRET: ${AUDIT_HMAC_SECRET:?Set AUDIT_HMAC_SECRET in .env}
    POSTGRES_DB: ${POSTGRES_DB:-platform}
    POSTGRES_USER: ${POSTGRES_USER:-platform}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-platform}
    POSTGRES_HOST: ${POSTGRES_HOST:-db}
    POSTGRES_PORT: ${POSTGRES_PORT:-5432}
    REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
    CACHE_URL: ${CACHE_URL:-redis://redis:6379/2}
```

> **Main change:** Replace `${DJANGO_SECRET_KEY:-change-me}` with `${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}`.
> This forces `docker compose` to fail if the variable is not set.

---

## Step 2: Update `compose.prod.yml`

**Location:** `compose.prod.yml:5-10`

```yaml
x-backend-prod-env: &backend_prod_env
  DJANGO_SETTINGS_MODULE: config.settings.prod
  DJANGO_DEBUG: "false"
  DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
  DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:?Set DJANGO_ALLOWED_HOSTS in .env}
  MFA_ENCRYPTION_KEYS: ${MFA_ENCRYPTION_KEYS:?Set MFA_ENCRYPTION_KEYS in .env}
  AUDIT_HMAC_SECRET: ${AUDIT_HMAC_SECRET:?Set AUDIT_HMAC_SECRET in .env}  # ✅ New
```

**Location:** `compose.prod.yml:33-35` (under `api`):

```yaml
api:
  environment:
    <<: *backend_prod_env
    METRICS_TOKEN: ${METRICS_TOKEN:?Set METRICS_TOKEN in .env}
    BACKUP_EXTERNAL_URI: ${BACKUP_EXTERNAL_URI:?Set BACKUP_EXTERNAL_URI in .env}
  # ✅ AUDIT_HMAC_SECRET comes from the anchor
```

---

## Step 3: Update `worker` and `beat` in compose.prod.yml

Ensure that `worker` and `beat` inherit `<<: *backend_prod_env` which now contains AUDIT_HMAC_SECRET.

---

## Step 4: Create/Update `.env.example`

**File:** `.env.example`

```bash
# ============================================
# MHAMI Production Environment Template
# ============================================
# Copy to .env and fill in real values.
# NEVER commit .env to source control.

# Django core
DJANGO_SECRET_KEY=                # python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=api.example.com,localhost  # comma-separated

# MFA encryption (Fernet)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
MFA_ENCRYPTION_KEYS=              # comma-separated Fernet keys for rotation

# Audit HMAC (hex-encoded, 64 chars)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
AUDIT_HMAC_SECRET=                # hex string for HMAC-SHA256 of audit chain

# Metrics
METRICS_TOKEN=                    # python -c "import secrets; print(secrets.token_urlsafe(32))"

# Backup
BACKUP_EXTERNAL_URI=              # s3://bucket/path or azure://container/path

# Database
POSTGRES_DB=platform
POSTGRES_USER=platform
POSTGRES_PASSWORD=                # strong password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0
CACHE_URL=redis://redis:6379/2
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Workers
GUNICORN_WORKERS=3
CELERY_WORKER_CONCURRENCY=2
CELERY_LOG_LEVEL=INFO

# Frontend
FRONTEND_PORT=8080
VITE_API_BASE=                    # optional: full origin if API on different host
```

---

## Step 5: Add CI Check

**File:** `.github/workflows/ci.yml`

Add a new job:

```yaml
  secrets-audit:
    name: Secrets Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - name: Check for default secrets in compose files
        run: |
          if grep -E "change-me|placeholder|example\.com" compose.yml compose.prod.yml; then
            echo "ERROR: Default secret found in compose file"
            exit 1
          fi
      - name: Verify required secrets in compose.prod.yml
        run: |
          required_secrets=(
            "DJANGO_SECRET_KEY"
            "AUDIT_HMAC_SECRET"
            "MFA_ENCRYPTION_KEYS"
            "METRICS_TOKEN"
            "BACKUP_EXTERNAL_URI"
            "DJANGO_ALLOWED_HOSTS"
          )
          for secret in "${required_secrets[@]}"; do
            if ! grep -q "$secret" compose.prod.yml; then
              echo "ERROR: Missing required secret $secret in compose.prod.yml"
              exit 1
            fi
          done
          echo "All required secrets present"
```

---

## Step 6: End-to-end Test

### 6.1 Create `.env.test`

```bash
cp .env.example .env.test
# Fill values safely (test keys only)
```

### 6.2 Run

```bash
docker compose -f compose.yml -f compose.prod.yml --env-file .env.test config --quiet
docker compose -f compose.yml -f compose.prod.yml --env-file .env.test up -d db redis api
sleep 10
curl http://localhost:8000/api/health/ready
```

### 6.3 Stop and clean up

```bash
 docker compose -f compose.yml -f compose.prod.yml --env-file .env.test down --remove-orphans
```

Do not use `down -v` for a shared or production-like environment. It removes
named volumes and can destroy data needed for diagnosis or recovery validation.
