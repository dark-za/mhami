# INFRA-01: Goal and Plan

## SMART Goal

> Within **1 week (5 working days)**, harden **every service** in
> `compose.prod.yml` (and the dev `compose.yml` for parity) to the same
> posture: non-root user, `cap_drop: [ALL]` + minimal `cap_add`,
> `read_only: true` + bounded `tmpfs`, `no-new-privileges`, bounded
> `pids_limit` / `mem_limit`, mandatory secrets fail-fast, explicit
> `healthcheck`, and `restart: unless-stopped`. Every container must run
> with **`id` ≠ 0** and **`capsh --print` must show only `cap_net_bind_service`**.

## Detailed Acceptance Standards

### Standard 1: Anchor parity

`compose.yml` and `compose.prod.yml` declare **byte-identical** `x-backend-defaults` blocks. A CI check (`scripts/ci/check_compose_anchor.sh`) diffs the two blocks and fails the build on drift.

### Standard 2: Per-service matrix

| Service | user | cap_drop | read_only | tmpfs | healthcheck | pids_limit | mem_limit |
|---|---|---|---|---|---|---|---|
| api | 1000:1000 | ALL + NET_BIND_SERVICE | ✓ | /tmp:50M | /api/health/live + /ready | 100 | 512m |
| worker | 1000:1000 | ALL + NET_BIND_SERVICE | ✓ | /tmp:50M | celery inspect ping | 200 | 512m |
| beat | 1000:1000 | ALL + NET_BIND_SERVICE | ✓ | /tmp:32M | process exists | 100 | 256m |
| db | 999:999 | ALL | ✓ | /tmp:64M + /run/postgresql | pg_isready | 200 | 1g |
| redis | 999:999 | ALL | ✓ | /tmp:32M | redis-cli ping | 100 | 512m |
| frontend | 1000:1000 | ALL | ✓ | /tmp:32M | wget / | 100 | 256m |
| nginx | 1000:1000 | ALL + NET_BIND_SERVICE | ✓ | /tmp:16M + /var/cache/nginx | curl /healthz | 100 | 128m |
| certbot | 1000:1000 | ALL | ✓ | /tmp:32M | certbot certificates | 50 | 128m |

### Standard 3: Mandatory secrets

Every secret in `compose.prod.yml` is declared with `${VAR:?Set VAR in .env}` — **no `:-change-me` defaults**, **no empty defaults**. The list:

```bash
DJANGO_SECRET_KEY
DJANGO_ALLOWED_HOSTS
MFA_ENCRYPTION_KEYS
AUDIT_HMAC_SECRET
METRICS_TOKEN
BACKUP_EXTERNAL_URI
POSTGRES_PASSWORD
```

### Standard 4: `DJANGO_DEBUG: "false"` is explicit

`compose.prod.yml` redeclares `DJANGO_DEBUG: "false"` even though `x-backend-prod-env` sets `DJANGO_SETTINGS_MODULE: config.settings.prod` (defense in depth).

### Standard 5: Healthcheck matrix

| Service | Healthcheck command | Interval | Timeout | Retries | Start period |
|---|---|---|---|---|---|
| api | `curl -fsS http://localhost:8000/api/health/live` | 30s | 5s | 3 | 30s |
| worker | `celery -A config.celery inspect ping -d celery@$HOSTNAME` | 60s | 10s | 3 | 60s |
| beat | `pgrep -f 'celery.*beat'` | 60s | 5s | 5 | 60s |
| db | `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` | 5s | 3s | 20 | 30s |
| redis | `redis-cli ping` | 5s | 3s | 20 | 5s |
| frontend | `wget -qO- http://localhost:80/ \| grep -q '<title>'` | 30s | 5s | 3 | 30s |
| nginx | `curl -fsS http://localhost:8080/healthz` | 30s | 5s | 3 | 30s |
| certbot | `certbot certificates` | 24h | 30s | 3 | 1h |

### Standard 6: Resource bounds

`mem_limit` and `pids_limit` are set on every service. The total stack limit is documented in `docs/SERVER_INVENTORY.md` and matches the production host's available resources.

---

## Detailed Implementation Plan

### Day 1 — Anchor parity + secrets

**Morning**
- [ ] Diff `x-backend-defaults` between `compose.yml` and `compose.prod.yml`.
- [ ] Move the source-of-truth into a single anchor and have both files reference it (or keep them in sync via `scripts/ci/check_compose_anchor.sh`).
- [ ] Promote every `:-change-me` to `${VAR:?Set VAR in .env}`.

**Afternoon**
- [ ] Add the CI check that fails on anchor drift.
- [ ] Document mandatory secrets in `docs/SECRET_MANAGEMENT.md`.

### Day 2 — Frontend + Nginx + Certbot

- [ ] Add `frontend` service to `compose.yml` with hardening.
- [ ] Add `nginx` service to `compose.yml` with hardening.
- [ ] Add `certbot` service to `compose.yml` (placeholder; full implementation in INFRA-05).

### Day 3 — read_only + tmpfs

- [ ] Add `read_only: true` + `tmpfs: [/tmp:50M]` to `worker` and `beat` in `compose.prod.yml`.
- [ ] Add `read_only: true` + `tmpfs: [/tmp:32M]` to `frontend` and `nginx`.
- [ ] Document the per-service tmpfs sizing.

### Day 4 — Healthcheck + restart

- [ ] Add `healthcheck` to every service.
- [ ] Confirm `restart: unless-stopped` everywhere.
- [ ] Add `logging:` driver with `max-size: 10m, max-file: 3`.

### Day 5 — Verify + docs

- [ ] Run `docker compose -f compose.yml -f compose.prod.yml config` and confirm clean.
- [ ] Run `docker compose -f compose.yml -f compose.prod.yml up -d` and confirm every healthcheck is green.
- [ ] Update `docs/SECRET_MANAGEMENT.md` and `CHANGELOG.md`.

---

## Dependency Graph

```
anchor parity (Day 1)
    ↓
mandatory secrets (Day 1)
    ↓
frontend + nginx + certbot services (Day 2)
    ↓
read_only + tmpfs (Day 3)
    ↓
healthcheck + restart (Day 4)
    ↓
docker compose config + up (Day 5)
    ↓
docs + CHANGELOG
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Anchor parity check green | DevOps |
| CP-2 | No `:-change-me` in compose.prod.yml | DevOps |
| CP-3 | frontend + nginx + certbot services added | DevOps |
| CP-4 | read_only + tmpfs on all backend services | DevOps |
| CP-5 | healthcheck on every service | DevOps |
| CP-6 | `docker compose config` clean | DevOps |
| CP-7 | `docker compose up -d` all healthy | DevOps |
| CP-8 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If `read_only: true` breaks a service that needs writable paths we missed → add a per-service `tmpfs`; do not relax the global posture.
- If `cap_drop: [ALL]` breaks a service that legitimately needs more caps (e.g. a debugging service) → add only the **minimum** `cap_add`; document the choice in `docs/SECRET_MANAGEMENT.md`.
- If `pids_limit: 100` is too tight for the worker under load → raise per service; do not raise globally.
