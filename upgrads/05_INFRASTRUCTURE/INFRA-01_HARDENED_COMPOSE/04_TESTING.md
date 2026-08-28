# INFRA-01: Test Strategy

> **Rule:** every check in this file is a real **runtime** assertion against a real `docker compose up` — not a static lint.

## 1. Unit Tests

Not applicable — INFRA-01 is a deployment-config change, not a feature.

## 2. Integration Tests

Not applicable.

## 3. End-to-End Tests

### 3.1 Static config check

```bash
docker compose -f compose.yml -f compose.prod.yml config -q
echo "Exit code: $LASTEXITCODE"
```

**Expected:** Exit code `0`, no `WARN` / `ERROR` on stderr.

### 3.2 Per-service hardening matrix

| Check | Command | Expected |
|---|---|---|
| All services have `cap_drop` | `docker compose ... config \| Select-String cap_drop` | ≥7 |
| All services have `security_opt` | `... config \| Select-String no-new-privileges` | ≥7 |
| All services have `pids_limit` | `... config \| Select-String pids_limit` | ≥7 |
| All services have `mem_limit` | `... config \| Select-String mem_limit` | ≥7 |
| All services have `healthcheck` | `... config \| Select-String healthcheck` | ≥7 |
| All backend services `read_only: true` | `... config \| Select-String read_only` | ≥5 |
| All services have `tmpfs: [/tmp]` | `... config \| Select-String /tmp:size` | ≥5 |

### 3.3 Runtime non-root check

```bash
docker compose -f compose.yml -f compose.prod.yml up -d api worker beat db redis
foreach ($svc in 'api','worker','beat','db','redis') {
  $id = docker compose -f compose.yml -f compose.prod.yml exec $svc id
  Write-Host "$svc: $id"
}
```

**Expected:**

```
api: uid=1000(user) gid=1000(user) groups=1000(user)
worker: uid=1000(user) gid=1000(user) groups=1000(user)
beat: uid=1000(user) gid=1000(user) groups=1000(user)
db: uid=999(postgres) gid=999(postgres) groups=999(postgres)
redis: uid=999(redis) gid=999(redis) groups=999(redis)
```

### 3.4 Runtime caps check

```bash
docker compose -f compose.yml -f compose.prod.yml exec api capsh --print
```

**Expected:** `Bounding` line contains only `cap_chown, cap_dac_override, cap_fowner, cap_fsetid, cap_kill, cap_setgid, cap_setuid, cap_setpcap, cap_net_bind_service, cap_net_raw, cap_sys_chroot, cap_mknod, cap_audit_write, cap_setfcap` (i.e. only `cap_net_bind_service` added on top of the docker default).

### 3.5 Healthcheck check

```bash
docker compose -f compose.yml -f compose.prod.yml ps
```

**Expected:** Every service `Up (healthy)` within 60s.

### 3.6 `pids_limit` enforced

```bash
docker compose -f compose.yml -f compose.prod.yml exec api cat /sys/fs/cgroup/pids.max
# Expected: 100
```

### 3.7 `read_only: true` enforced

```bash
docker compose -f compose.yml -f compose.prod.yml exec api touch /etc/passwd
echo "Exit code: $LASTEXITCODE"
# Expected: 1 (Read-only file system)
```

### 3.8 Mandatory secrets fail-fast

```bash
# unset all mandatory secrets, then try to up
env -i PATH=$PATH docker compose -f compose.yml -f compose.prod.yml up -d api 2>&1 | Out-String
echo "Exit code: $LASTEXITCODE"
# Expected: non-zero (variable not set)
```

### 3.9 Anchor parity

```bash
bash scripts/ci/check_compose_anchor.sh
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| Static config | 1 | exit 0 |
| Hardening matrix | 7 | all present |
| Runtime non-root | 5 | uid ≠ 0 |
| Runtime caps | 1 | only NET_BIND_SERVICE |
| Healthcheck | 7 | all Up (healthy) |
| pids_limit | 1 | 100 |
| read_only | 1 | exit 1 on /etc/passwd |
| Mandatory secrets | 1 | exit non-zero when unset |
| Anchor parity | 1 | exit 0 |

---

## 5. Run Tests

### 5.1 Local

```bash
docker compose -f compose.yml -f compose.prod.yml up -d
bash scripts/ci/check_compose_anchor.sh
docker compose -f compose.yml -f compose.prod.yml exec api id
docker compose -f compose.yml -f compose.prod.yml exec api capsh --print
docker compose -f compose.yml -f compose.prod.yml ps
```

### 5.2 CI

The `compose-anchor` job in `.github/workflows/ci.yml` runs the parity check on every PR. The `backend` job (existing) runs the integration tests under the hardened compose stack.

### 5.3 Failure simulation

To prove the anchor check works, intentionally drift the two files:

```bash
# In compose.yml, change pids_limit from 100 to 200
bash scripts/ci/check_compose_anchor.sh
echo "Exit code: $LASTEXITCODE"
# Expected: 1
```

Revert the change afterwards.

---

## 6. Cross-links

- [INFRA-02 — CSP](..) — nginx service introduced here is the policy enforcer.
- [INFRA-05 — Let's Encrypt](..) — certbot service is a placeholder here; full implementation in INFRA-05.
- [upgrads/01_CRITICAL_FIXES/C-02_PRODUCTION_SECRETS](../../01_CRITICAL_FIXES/C-02_PRODUCTION_SECRETS/00_DISCOVERY.md) — fail-fast secrets.
