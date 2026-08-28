# C-02: Fix Missing Production Secrets (Production Secrets Missing)

## 1. Discovery Summary

### Current State

**Problem:** `compose.yml` and `compose.prod.yml` do not pass `AUDIT_HMAC_SECRET`, which leads to `ImproperlyConfigured` when starting Production.

**Guide:**

`backend/config/settings/base.py:43-47`:
```python
if (
    settings.django_settings_module == "config.settings.prod"
    and (not settings.audit_hmac_secret or settings.audit_hmac_secret == "change-me")
):
    raise ImproperlyConfigured(
        "AUDIT_HMAC_SECRET must be set to a non-default value in production."
    )
```

`compose.yml:31-34`:
```yaml
DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:-change-me}
DJANGO_DEBUG: ${DJANGO_DEBUG:-true}
DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,api}
MFA_ENCRYPTION_KEYS: ${MFA_ENCRYPTION_KEYS:-}
# ❌ No AUDIT_HMAC_SECRET
```

`compose.prod.yml:5-9`:
```yaml
x-backend-prod-env: &backend_prod_env
  DJANGO_SETTINGS_MODULE: config.settings.prod
  DJANGO_DEBUG: "false"
  DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
  DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:?Set DJANGO_ALLOWED_HOSTS in .env}
  MFA_ENCRYPTION_KEYS: ${MFA_ENCRYPTION_KEYS:?Set MFA_ENCRYPTION_KEYS in .env}
  # ❌ No AUDIT_HMAC_SECRET
```

### Impact

| Dimension | Impact |
|---|---|
| Functional | Production Compose fails to start with `ImproperlyConfigured` |
| Security | Without HMAC secret, the Audit chain loses its second protection layer |
| Operational | Production cannot be deployed |
| Compliance | Violates base.py:43-47 (fail-fast security) |

### Reproducible Evidence

```bash
grep "AUDIT_HMAC_SECRET" compose.yml
grep "AUDIT_HMAC_SECRET" compose.prod.yml
# Both return zero results

docker compose -f compose.yml -f compose.prod.yml config | grep -i audit
# Does not mention AUDIT_HMAC_SECRET
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Secrets in compose.yml | 4 (DJANGO_*, MFA) | 5 (with AUDIT_HMAC_SECRET) |
| fail-fast | 3 variables | 4 variables |
| BACKUP_EXTERNAL_URI | Exists in prod | Mandatory + used |
| METRICS_TOKEN | Exists in prod | Mandatory + verified |
| Secret verification in CI | Nonexistent | CI step that checks for absence of "change-me" |

---

## 3. Goal

> Within **2 days**, ensure that **all** sensitive secrets are explicitly defined in `compose.yml` and `compose.prod.yml`, and that the build fails in CI if default values remain.

### Acceptance Standards

1. **AC-1:** `AUDIT_HMAC_SECRET` exists in `compose.yml` and `compose.prod.yml`.
2. **AC-2:** `docker compose config` validates the variable without error.
3. **AC-3:** `docker compose --env-file .env.test up` starts successfully in staging.
4. **AC-4:** CI verifies that "change-me" does not exist in any compose.
5. **AC-5:** `docs/SECRET_MANAGEMENT.md` documents all mandatory variables.

---

## 4. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Breaking staging | Medium | High | Test in staging first |
| Secret leakage in Git | Low | High | .env.example + .gitignore |
| Rotation difficulty | Medium | Medium | Documentation rotation procedure |

---

## 5. Sub-tasks

- [ ] Add AUDIT_HMAC_SECRET to compose.yml and compose.prod.yml
- [ ] Update .env.example with all variables
- [ ] Add CI step to verify absence of defaults
- [ ] Test `docker compose config`
- [ ] Update docs/SECRET_MANAGEMENT.md
- [ ] Test full staging startup
