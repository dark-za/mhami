# Secret Management

## Rules

- No real secrets in Git.
- No secrets in logs, browser code, or release notes.
- Production secrets live outside the repository in a protected location.
- Access is least-privilege and service-specific.
- Secret rotation and revocation must be documented before runtime work.

## Required production secrets

The following variables are **mandatory** in production. `compose.prod.yml`
references each with the fail-fast `${VAR:?Set VAR in .env}` syntax so a
missing or empty value prevents the stack from booting.

| Variable | Used by | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | `api`, `worker`, `beat` | Long random string, never "change-me". Rotating invalidates all Django sessions. |
| `DJANGO_ALLOWED_HOSTS` | `api` | Comma-separated hostnames. Misconfiguration leads to 400 responses in browsers. |
| `MFA_ENCRYPTION_KEYS` | `api` | Comma-separated Fernet keys. See MFA section below. |
| `AUDIT_HMAC_SECRET` | `api`, `worker`, `beat` | Independent of `DJANGO_SECRET_KEY`. Protects the audit chain HMAC. |
| `METRICS_TOKEN` | `api` | Bearer token for the metrics endpoint. Rotate quarterly. |
| `BACKUP_EXTERNAL_URI` | `api`, `worker`, `beat` | URL of the encrypted off-site backup destination. |
| `CODECOV_TOKEN` | CI | Codecov upload token for backend and frontend coverage. |

`AUDIT_HMAC_SECRET` is also mandatory in development: `compose.yml` now
references it with the same fail-fast syntax. The dev value can be the
literal `.env` value, but a default placeholder such as `change-me` is
rejected by CI and the application check.

## CI enforcement

`.github/workflows/ci.yml` contains a `Verify no default secrets in
compose` step that fails the build if any of the strings `change-me`,
`replace-with-a-long`, or `replace-with-approved` appear inside
`compose.yml`, `compose.prod.yml`, or any file under `infra/`. The same
step asserts that `AUDIT_HMAC_SECRET` is declared in both compose files.

## Rotation procedure

1. Generate the new value outside the repository and inject it via the
   secret manager that supplies the `.env` file.
2. Redeploy the affected services (`api`, `worker`, `beat`) so the new
   value takes effect.
3. Run the smoke-test suite (login, audit verification, MFA challenge,
   backup dry-run) and confirm a green run.
4. Record the rotation in the change log with operator name and date.
5. Revoke the old value only after step 3 succeeds.

## MFA encryption keys

- `MFA_ENCRYPTION_KEYS` is mandatory in production and must be independent from `DJANGO_SECRET_KEY`.
- Keys use the Fernet URL-safe base64 format. Generate a key with
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- The first comma-separated key encrypts new values. Remaining keys are decrypt-only rotation keys.
- To rotate, prepend the new key, deploy, run `python manage.py rotate_mfa_secrets`, verify MFA login,
  then remove retired keys in a later controlled deployment.
- Never remove an old key before the rotation command and MFA verification complete.

## Audit chain HMAC

- `AUDIT_HMAC_SECRET` is read in `config/settings/base.py` and used by
  `apps.audit.services.record_audit_event` to compute the per-event
  `event_hash`.
- The default fallback (`SECRET_KEY`) is intentionally not allowed in
  production: an attacker that learns the Django secret must not be
  able to forge audit events.
- Rotation invalidates the historical chain hash check. After rotation,
  re-anchor the chain via the dedicated `audit_reanchor` management
  command and record the new anchor in the audit log.
