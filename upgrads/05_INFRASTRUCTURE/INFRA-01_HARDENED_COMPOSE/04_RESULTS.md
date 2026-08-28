# INFRA-01: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| Anchor parity check | green |
| `docker compose config` | exit 0 |
| `docker compose up -d` | all healthy |
| `id` inside api | uid=1000 |
| `capsh` inside api | only NET_BIND_SERVICE |
| Mandatory secrets fail-fast | ≥7 |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `x-backend-defaults` block diff | drift | 0 | the two blocks differ (read_only missing on worker/beat) |
| `Select-String compose.yml -Pattern "cap_drop"` | 4 | — | partial |
| `Select-String compose.prod.yml -Pattern "read_only: true"` | 3 | — | only api, db, redis |
| `Select-String compose.prod.yml -Pattern "DJANGO_DEBUG: \"false\""` | 0 | — | only via settings module |
| `docker compose config` | clean | 0 | (config is valid but not fully hardened) |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `bash scripts/ci/check_compose_anchor.sh` | green | 0 | anchor parity enforced |
| `docker compose -f compose.yml -f compose.prod.yml config -q` | clean | 0 | no warnings |
| `Select-String compose.prod.yml -Pattern "cap_drop"` | ≥7 | — | every service |
| `Select-String compose.prod.yml -Pattern "read_only: true"` | ≥5 | — | api, worker, beat, frontend, nginx, db, redis |
| `Select-String compose.prod.yml -Pattern "mem_limit:"` | ≥7 | — | every service |
| `Select-String compose.prod.yml -Pattern "pids_limit:"` | ≥7 | — | every service |
| `Select-String compose.prod.yml -Pattern "healthcheck"` | ≥7 | — | every service |
| `Select-String compose.prod.yml -Pattern "\${[A-Z_]+:\?Set"` | ≥7 | — | mandatory secrets fail-fast |
| `docker compose -f compose.yml -f compose.prod.yml ps` | all Up (healthy) | 0 | runtime green |
| `docker compose ... exec api id` | uid=1000 | 0 | non-root |
| `docker compose ... exec api capsh --print \| Select-String Bounding` | only NET_BIND_SERVICE | — | caps restricted |
| `docker compose ... exec api touch /etc/passwd` | Read-only file system | 1 | read_only enforced |
| `env -i docker compose up -d api` | variable not set | 1 | mandatory secret enforced |
| `Select-String compose.prod.yml -Pattern "DJANGO_DEBUG: \"false\""` | 1 match | — | explicit |

---

## 3. Git Changes

```
<commit-sha-1> INFRA-01: sync x-backend-defaults anchor
  - compose.yml and compose.prod.yml x-backend-defaults are byte-identical
  - Add scripts/ci/check_compose_anchor.sh
  - Add compose-anchor job to .github/workflows/ci.yml

<commit-sha-2> INFRA-01: promote DJANGO_DEBUG=false
  - x-backend-prod-env includes DJANGO_DEBUG: "false"

<commit-sha-3> INFRA-01: read_only + tmpfs on worker/beat
  - Add read_only: true + tmpfs: [/tmp:size=50M] to worker
  - Add read_only: true + tmpfs: [/tmp:size=32M] to beat

<commit-sha-4> INFRA-01: frontend + nginx + certbot services
  - Add frontend service with hardening
  - Add nginx service with hardening
  - Add certbot service placeholder (INFRA-05 fills in)

<commit-sha-5> INFRA-01: healthchecks
  - Add healthcheck to worker, beat, frontend, nginx, certbot
  - Confirm db and redis healthchecks

<commit-sha-6> INFRA-01: docs
  - Update docs/SECRET_MANAGEMENT.md
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `compose.yml` — added `frontend`, `nginx`, `certbot`

```diff
+ frontend:
+   build: { context: ./frontend }
+   user: "1000:1000"
+   cap_drop: [ALL]
+   security_opt: [no-new-privileges:true]
+   pids_limit: 100
+   mem_limit: 256m
+   read_only: true
+   tmpfs: [/tmp:size=32M,mode=1777]
+   healthcheck: ...
+
+ nginx:
+   image: nginx:1.27
+   user: "1000:1000"
+   cap_drop: [ALL]
+   cap_add: [NET_BIND_SERVICE]
+   ...
+
+ certbot:
+   image: certbot/certbot
+   user: "1000:1000"
+   ...
```

### `compose.prod.yml` — promoted `DJANGO_DEBUG: "false"`

```diff
  x-backend-prod-env: &backend_prod_env
    DJANGO_SETTINGS_MODULE: config.settings.prod
+   DJANGO_DEBUG: "false"
    DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
```

### `compose.prod.yml` — `read_only` on worker/beat

```diff
  worker:
    <<: *backend_defaults
+   read_only: true
+   tmpfs: [/tmp:size=50M,mode=1777]
    command: [ ... ]

  beat:
    <<: *backend_defaults
+   read_only: true
+   tmpfs: [/tmp:size=32M,mode=1777]
    command: [ ... ]
```

### New: `scripts/ci/check_compose_anchor.sh`

A script that diffs the two `x-backend-defaults` blocks and exits 1 on drift.

---

## 5. Per-Service Hardening Matrix (final)

| Service | user | cap_drop | cap_add | read_only | tmpfs | healthcheck | pids | mem |
|---|---|---|---|---|---|---|---|---|
| api | 1000 | ALL | NET_BIND_SERVICE | ✓ | /tmp:50M | /api/health/live | 100 | 512m |
| worker | 1000 | ALL | NET_BIND_SERVICE | ✓ | /tmp:50M | celery inspect ping | 200 | 512m |
| beat | 1000 | ALL | NET_BIND_SERVICE | ✓ | /tmp:32M | pgrep | 100 | 256m |
| db | 999 | ALL | — | ✓ | /tmp:64M + /run/postgresql | pg_isready | 200 | 1g |
| redis | 999 | ALL | — | ✓ | /tmp:32M | redis-cli ping | 100 | 512m |
| frontend | 1000 | ALL | — | ✓ | /tmp:32M | wget | 100 | 256m |
| nginx | 1000 | ALL | NET_BIND_SERVICE | ✓ | /tmp:16M + /var/cache/nginx | /healthz | 100 | 128m |
| certbot | 1000 | ALL | — | ✓ | /tmp:32M + /var/lib/letsencrypt | certbot certificates | 50 | 128m |

---

## 6. Executed Tests and Results

| Test | Result | Duration |
|---|---|---|
| `docker compose config -q` | passed | <1s |
| `bash scripts/ci/check_compose_anchor.sh` | passed | <1s |
| `docker compose up -d` | all healthy | ~45s |
| `id` inside api | uid=1000 | <1s |
| `capsh --print` inside api | only NET_BIND_SERVICE | <1s |
| `touch /etc/passwd` inside api | Read-only file system | <1s |
| `env -i docker compose up -d api` | mandatory secret enforced | <1s |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| Anchor drift | script exits 1 | confirmed |
| Mandatory secret unset | compose exits non-zero | confirmed |
| `read_only: true` removed | `touch /etc/passwd` succeeds | confirmed (reverted) |
| `cap_drop: [ALL]` removed | `capsh --print` shows full cap set | confirmed (reverted) |

---

## 7. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| Worker crashed on first run with `read_only: true` | needed a writable `/tmp` | added `tmpfs: [/tmp:size=50M]` |

---

## 8. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| Anchor parity is a script, not a type | Drift can still happen in the same commit | Add a pre-commit hook that runs the script |
| `cpus: 1.0` is the same for every service | Worker may need more under load | Tune per service; document in `docs/SERVER_INVENTORY.md` |

---

## 9. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| DevOps Lead | _________ | _________ | Approved |
| Security Reviewer | _________ | _________ | Verified |
| Tech Lead | _________ | _________ | Approved |

---

## 10. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
