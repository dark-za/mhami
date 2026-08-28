# C-02: Verification Commands

## Phase 1: Proving the Problem (Pre-Fix)

### Command 1.1: Confirm absence of AUDIT_HMAC_SECRET

```bash
Select-String -Path compose.yml,compose.prod.yml -Pattern "AUDIT_HMAC_SECRET"
```

**Expected output:** No results (exit 0 but empty).

### Command 1.2: Attempt to start Production

```bash
# simulation without .env
docker compose -f compose.yml -f compose.prod.yml up api
```

**Expected output:**
```
django.core.exceptions.ImproperlyConfigured: AUDIT_HMAC_SECRET must be set to a non-default value in production.
```

### Command 1.3: Examine existing secrets

```bash
grep -E "^\s+[A-Z_]+:" compose.yml | head -20
```

**Expected output:** DJANGO_*, MFA_*, POSTGRES_*, REDIS_URL (no AUDIT_HMAC).

---

## Phase 2: Verifying the Solution (Post-Fix)

### Command 2.1: Confirm presence of AUDIT_HMAC_SECRET

```bash
grep "AUDIT_HMAC_SECRET" compose.yml compose.prod.yml
```

**Expected output:** at least two lines.

### Command 2.2: docker compose config validation

```bash
# with .env.test
docker compose -f compose.yml -f compose.prod.yml --env-file .env.test config --quiet
```

**Expected output:** `exit code 0`.

### Command 2.3: CI secret verification

```bash
# must fail if "change-me" remains
! grep -q "change-me" compose.yml compose.prod.yml
echo "OK"
```

**Expected output:** `OK`.

### Command 2.4: Run API and verify logs

```bash
docker compose -f compose.yml -f compose.prod.yml up -d api
docker compose logs api | grep -i "starting\|ready\|error"
```

**Expected output:** `Starting development server` or `Booting worker` without `ImproperlyConfigured`.

### Command 2.5: health check

```bash
curl http://localhost:8000/api/health/ready
```

**Expected output:** `{"status": "ready"}`.
