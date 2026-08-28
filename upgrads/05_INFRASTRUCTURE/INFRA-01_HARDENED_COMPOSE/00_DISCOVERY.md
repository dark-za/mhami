# INFRA-01: Hardened Production Compose

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The production Compose file must run every service with a **defense-in-depth** posture: non-root user, dropped capabilities, read-only root filesystem where possible, bounded resources, no-new-privileges, mandatory secrets (no defaults), and an explicit health check. While the project has the `x-backend-defaults` anchor pattern in `compose.yml` and `compose.prod.yml`, several **gaps remain** that the C-02 audit and INFRA-01 ticket call out.

**Evidence gathered:**
- `compose.yml` line 7: `x-backend-defaults` already has `user: "1000:1000"`, `cap_drop: [ALL]`, `cap_add: [NET_BIND_SERVICE]`, `security_opt: [no-new-privileges:true]`, `pids_limit: 100`, `mem_limit: 512m`, `cpus: 1.0`.
- `compose.prod.yml` line 28: `x-backend-prod-env` enforces `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `MFA_ENCRYPTION_KEYS`, `AUDIT_HMAC_SECRET` with `${VAR:?...}` fail-fast syntax.
- `compose.prod.yml` line 39: `x-backend-restart` adds `read_only: true` and `tmpfs: [/tmp:size=50M]`.
- Gaps that remain:
  - The dev `compose.yml` still allows `DJANGO_DEBUG: ${DJANGO_DEBUG:-true}` (correct for dev, but **the override is not promoted** to enforce `false` in `compose.prod.yml`).
  - The `frontend` service in `compose.yml` does not apply `read_only: true` (acceptable for the dev container, but must be hardened in prod).
  - The `nginx` service is not present in `compose.yml` (lives only in infra/nginx) — needs a `service:` block with its own hardening.
  - The `worker` and `beat` services in `compose.prod.yml` are missing the `read_only: true` override.
  - The `BACKUP_EXTERNAL_URI` and `METRICS_TOKEN` are mandatory in `compose.prod.yml` for `api`, but **not for `worker` / `beat`** (they don't need BACKUP_EXTERNAL_URI, but they do need `METRICS_TOKEN` if they emit metrics).

### Impact

| Dimension | Impact |
|---|---|
| Functional | A single un-hardened service is an entry point. |
| Security | Drop-the-default audit logging / `:-change-me` would let `DJANGO_SECRET_KEY` slip into prod. |
| Operational | No `healthcheck` → orchestrator cannot detect a hung process. |
| Compliance | PDPL and Gate-B require non-root, no-new-privileges, read-only root, and bounded resources. |

### Reproducible Evidence

```bash
# 1. Confirm the anchor is shared between compose.yml and compose.prod.yml
Select-String -Path compose.yml -Pattern "x-backend-defaults"
Select-String -Path compose.prod.yml -Pattern "x-backend-defaults"

# 2. Confirm cap_drop is on every backend service
Select-String -Path compose.yml -Pattern "cap_drop"
Select-String -Path compose.prod.yml -Pattern "cap_drop"

# 3. Confirm healthcheck on api, worker, beat
Select-String -Path compose.yml -Pattern "healthcheck"
Select-String -Path compose.prod.yml -Pattern "healthcheck"

# 4. Confirm mandatory secrets
Select-String -Path compose.prod.yml -Pattern "\${[A-Z_]+:\?Set"
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `x-backend-defaults` anchor | present | unchanged (already hardened) |
| `read_only: true` on backend services | api only | api, worker, beat, db, redis |
| `tmpfs: [/tmp]` | api, db, redis | worker, beat too |
| `cap_drop: [ALL]` | api, worker, beat, db, redis | frontend, nginx too |
| Mandatory secrets fail-fast | api | api, worker, beat |
| `DJANGO_DEBUG=false` enforced in prod | via `DJANGO_SETTINGS_MODULE=prod` | also via explicit `DJANGO_DEBUG: "false"` |
| Frontend hardening | not in compose | `read_only`, `cap_drop`, `no-new-privileges` |
| Nginx hardening | not in compose | `cap_drop: [ALL]`, `cap_add: [NET_BIND_SERVICE]`, `read_only`, no-new-privileges |
| `mem_limit` / `pids_limit` on all services | partial | universal |
| `healthcheck` on all services | partial | universal (api, worker, beat, db, redis, frontend, nginx) |

---

## 3. Goal Statement

> Within **1 week (5 working days)**, harden **every service** in `compose.prod.yml` (and the dev `compose.yml` for parity) to the same posture: `user: 1000:1000` (or service-specific UID), `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, `pids_limit`, `mem_limit`, `read_only: true` + bounded `tmpfs` where possible, mandatory secrets fail-fast, explicit `healthcheck`, and `restart: unless-stopped`.

### Acceptance Criteria

1. **AC-1:** `x-backend-defaults` in `compose.yml` and `compose.prod.yml` are byte-identical.
2. **AC-2:** Every service in `compose.prod.yml` (api, worker, beat, db, redis, frontend, nginx, certbot) has `cap_drop`, `security_opt`, `pids_limit`, `mem_limit`, and `healthcheck`.
3. **AC-3:** `read_only: true` + bounded `tmpfs` is applied to api, worker, beat, db, redis, frontend, nginx.
4. **AC-4:** All mandatory secrets use `${VAR:?Set VAR in .env}` (no `:-change-me`).
5. **AC-5:** `DJANGO_DEBUG` is set to `"false"` explicitly in `compose.prod.yml` (not via `dev` default).
6. **AC-6:** `docker compose -f compose.yml -f compose.prod.yml config` exits 0 with no warnings about unresolved variables.
7. **AC-7:** `docker compose -f compose.yml -f compose.prod.yml up -d` boots cleanly and every `healthcheck` reports `healthy` within 60s.
8. **AC-8:** `ps aux | grep -E 'root|UID'` inside the running `api` container returns a non-root user.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Anchor drift between `compose.yml` and `compose.prod.yml` | High | High | Generate `compose.prod.yml` from a CI check that diffs the two `x-backend-defaults` blocks. |
| Service breaks under `read_only: true` | Medium | High | Add per-service `tmpfs` for `/tmp` and any other writable path. |
| Healthcheck uses an endpoint that requires auth | Medium | Medium | Use `/api/health/live` (unauthenticated liveness) and `/api/health/ready` (readiness, may require auth). |
| `pids_limit: 100` is too tight for the worker | Medium | Medium | Tune per service; document the choice. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Sync `x-backend-defaults` between `compose.yml` and `compose.prod.yml` | DevOps | not-started |
| 2 | Add `frontend` service to `compose.yml` with hardening | DevOps | not-started |
| 3 | Add `nginx` service to `compose.yml` with hardening | DevOps | not-started |
| 4 | Add `certbot` service to `compose.yml` (cross-link INFRA-05) | DevOps | not-started |
| 5 | Promote `DJANGO_DEBUG: "false"` in `compose.prod.yml` | DevOps | not-started |
| 6 | Add `healthcheck` to every service | DevOps | not-started |
| 7 | Add `read_only: true` + `tmpfs` to worker, beat, frontend, nginx | DevOps | not-started |
| 8 | Run `docker compose config` and `up -d` to verify | DevOps | not-started |
| 9 | Update `docs/SECRET_MANAGEMENT.md` and `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [compose.yml](../../../compose.yml)
- [compose.prod.yml](../../../compose.prod.yml)
- [infra/docker/README.md](../../../infra/docker/README.md)
- [docs/SECRET_MANAGEMENT.md](../../../docs/SECRET_MANAGEMENT.md)
- [upgrads/01_CRITICAL_FIXES/C-02_PRODUCTION_SECRETS](../../01_CRITICAL_FIXES/C-02_PRODUCTION_SECRETS/00_DISCOVERY.md) — share the secret-fail-fast pattern
- [upgrads/05_INFRASTRUCTURE/INFRA-05_LETS_ENCRYPT](..) — certbot service depends on this
