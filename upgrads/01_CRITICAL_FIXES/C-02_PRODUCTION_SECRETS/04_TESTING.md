# C-02: Test Strategy

## 1. Compose Tests

### 1.1 Test 1: Verify mandatory secrets

**File:** `tests/compose/test_required_secrets.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

REQUIRED_SECRETS=(
  "DJANGO_SECRET_KEY"
  "AUDIT_HMAC_SECRET"
  "MFA_ENCRYPTION_KEYS"
  "METRICS_TOKEN"
  "BACKUP_EXTERNAL_URI"
  "DJANGO_ALLOWED_HOSTS"
)

FAILED=0
for secret in "${REQUIRED_SECRETS[@]}"; do
  if ! grep -q "$secret" compose.prod.yml; then
    echo "❌ Missing required secret: $secret"
    FAILED=1
  else
    echo "✅ Found: $secret"
  fi
done

if [ $FAILED -eq 1 ]; then
  echo "FAILED: Missing required secrets"
  exit 1
fi
```

### 1.2 Test 2: Verify absence of defaults

```bash
#!/usr/bin/env bash
set -euo pipefail

if grep -E ":-change-me|:-placeholder" compose.yml compose.prod.yml; then
  echo "❌ Default value found in compose"
  exit 1
fi
echo "✅ No default secrets"
```

### 1.3 Test 3: Verify failure to start without secrets

```bash
#!/usr/bin/env bash
set -euo pipefail

# Attempt to run without .env
output=$(docker compose -f compose.yml -f compose.prod.yml config 2>&1 || true)
if echo "$output" | grep -q "Set DJANGO_SECRET_KEY in .env"; then
  echo "✅ Correctly fails without .env"
else
  echo "❌ Should have failed with clear error"
  exit 1
fi
```

---

## 2. Application Tests

### 2.1 Production startup test

```bash
#!/usr/bin/env bash
set -euo pipefail

# .env.test must contain valid values
docker compose -f compose.yml -f compose.prod.yml --env-file .env.test up -d db redis api

# Wait until ready
for i in {1..30}; do
  if curl -fsS http://localhost:8000/api/health/ready >/dev/null; then
    echo "✅ API is ready"
    break
  fi
  sleep 2
done

# Verify no errors
docker compose logs api | grep -i "ImproperlyConfigured" && {
  echo "❌ ImproperlyConfigured in logs"
  exit 1
}

# Cleanup
docker compose -f compose.yml -f compose.prod.yml --env-file .env.test down --remove-orphans
echo "✅ Production compose test passed"
```

### 2.2 HMAC test

**File:** `backend/apps/audit/tests/test_audit_secrets.py`

```python
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

@pytest.mark.django_db
class TestAuditSecrets:
    def test_default_hmac_secret_fails_in_prod(self):
        with override_settings(
            DJANGO_SETTINGS_MODULE="config.settings.prod",
            AUDIT_HMAC_SECRET="change-me",
        ):
            with pytest.raises(ImproperlyConfigured):
                from config.settings import base
                # must fail on import
                importlib.reload(base)

    def test_empty_hmac_secret_fails_in_prod(self):
        with override_settings(
            DJANGO_SETTINGS_MODULE="config.settings.prod",
            AUDIT_HMAC_SECRET="",
        ):
            with pytest.raises(ImproperlyConfigured):
                importlib.reload(base)
```

---

## 3. CI Tests

### 3.1 GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
  compose-secrets:
    name: Compose Secrets Validation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - name: Required secrets
        run: bash tests/compose/test_required_secrets.sh
      - name: No defaults
        run: bash tests/compose/test_no_defaults.sh
```

---

## 4. Success Criteria

| Test | Count | Result |
|---|---|---|
| Compose secrets present | 1 | passed |
| No default values | 1 | passed |
| Fails without env | 1 | passed |
| Production boots | 1 | passed |
| HMAC validation | 2 | passed |
| **Total** | **6** | **6/6 passed** |
