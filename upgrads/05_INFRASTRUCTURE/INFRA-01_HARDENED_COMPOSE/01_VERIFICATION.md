# INFRA-01: Verification Commands

> **Instructions:** Run the baseline (Phase 1) before the change, then the post-fix (Phase 2) to confirm hardening is in place.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Compare `x-backend-defaults` between files

```bash
$yml = Get-Content compose.yml -Raw
$prod = Get-Content compose.prod.yml -Raw
$ymlBlock = ($yml -split "x-backend-defaults: &backend_defaults", 2)[1].Split("`n`n")[0]
$prodBlock = ($prod -split "x-backend-defaults: &backend_defaults", 2)[1].Split("`n`n")[0]
$ymlBlock -eq $prodBlock
# Expected: True
```

### Command 1.2 — `cap_drop` is on every backend service

```bash
Select-String -Path compose.yml -Pattern "cap_drop" | Measure-Object | Select-Object -ExpandProperty Count
# Expected: 4 (api, worker, beat, db, redis — anchor covers api/worker/beat, db/redis inline)
```

### Command 1.3 — `read_only: true` only on api

```bash
Select-String -Path compose.prod.yml -Pattern "read_only: true" | Measure-Object | Select-Object -ExpandProperty Count
# Expected: 3 (api via x-backend-restart, db, redis) — but worker/beat are missing
```

### Command 1.4 — `healthcheck` on every service

```bash
Get-Content compose.yml | Select-String -Pattern "^\s{2}(api|worker|beat|db|redis|frontend|nginx|certbot):" | ForEach-Object {
  $svc = ($_.Matches.Value -replace ":\s*$", "").Trim()
  $hasHc = (Get-Content compose.yml -Raw) -match "(?ms)${svc}:.*?healthcheck:"
  [PSCustomObject]@{ Service = $svc; Healthcheck = $hasHc }
}
# Expected: every row Healthcheck = True
```

### Command 1.5 — Mandatory secrets fail-fast

```bash
Select-String -Path compose.prod.yml -Pattern "\${[A-Z_]+:\?Set" | Measure-Object | Select-Object -ExpandProperty Count
# Expected: ≥6 (DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, MFA_ENCRYPTION_KEYS, AUDIT_HMAC_SECRET, METRICS_TOKEN, BACKUP_EXTERNAL_URI)
```

### Command 1.6 — `DJANGO_DEBUG` enforced in prod

```bash
Select-String -Path compose.prod.yml -Pattern "DJANGO_DEBUG: \"false\""
# Expected: at least 1 match
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — `docker compose config` is clean

```bash
docker compose -f compose.yml -f compose.prod.yml config 2>&1 | Out-String | Select-Object -First 30
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### Command 2.2 — `cap_drop` is on every service

```bash
docker compose -f compose.yml -f compose.prod.yml config --services | ForEach-Object {
  $svc = $_
  $has = docker compose -f compose.yml -f compose.prod.yml config | Select-String -Pattern "(?ms)${svc}:.*?cap_drop" -Quiet
  [PSCustomObject]@{ Service = $svc; CapDrop = $has }
}
# Expected: every row CapDrop = True
```

### Command 2.3 — `read_only: true` on api/worker/beat/frontend/nginx

```bash
docker compose -f compose.yml -f compose.prod.yml config --services | ForEach-Object {
  $svc = $_
  $has = docker compose -f compose.yml -f compose.prod.yml config | Select-String -Pattern "(?ms)${svc}:.*?read_only: true" -Quiet
  [PSCustomObject]@{ Service = $svc; ReadOnly = $has }
}
# Expected: api, worker, beat, frontend, nginx ReadOnly = True
```

### Command 2.4 — `healthcheck` on every service

```bash
docker compose -f compose.yml -f compose.prod.yml config --services | ForEach-Object {
  $svc = $_
  $has = docker compose -f compose.yml -f compose.prod.yml config | Select-String -Pattern "(?ms)${svc}:.*?healthcheck" -Quiet
  [PSCustomObject]@{ Service = $svc; Healthcheck = $has }
}
# Expected: every row Healthcheck = True
```

### Command 2.5 — Container runs as non-root

```bash
docker compose -f compose.yml -f compose.prod.yml up -d api
docker compose -f compose.yml -f compose.prod.yml exec api id
# Expected: uid=1000(user) gid=1000(user) groups=1000(user)
```

### Command 2.6 — Healthcheck passes

```bash
docker compose -f compose.yml -f compose.prod.yml ps
# Expected: every service "Up (healthy)"
```

### Command 2.7 — `pids_limit` enforced

```bash
docker compose -f compose.yml -f compose.prod.yml exec api cat /sys/fs/cgroup/pids.max 2>/dev/null
# Expected: 100
```

### Command 2.8 — `cap_drop` enforced at runtime

```bash
docker compose -f compose.yml -f compose.prod.yml exec api capsh --print | Select-String "Bounding"
# Expected: cap_chown, cap_dac_override, cap_fowner, cap_fsetid, cap_kill, cap_setgid, cap_setuid, cap_setpcap, cap_net_bind_service, cap_net_raw, cap_sys_chroot, cap_mknod, cap_audit_write, cap_setfcap
# (i.e. only NET_BIND_SERVICE is left)
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Existing services still boot

```bash
docker compose -f compose.yml up -d
docker compose -f compose.yml ps
# Expected: all Up (healthy)
```

### Command 3.2 — Backup job still runs (cross-link INFRA-03)

```bash
docker compose -f compose.yml exec backend python manage.py shell -c "from apps.backups.services import run_backup; print(run_backup())"
# Expected: <BackupRun: ...> or "Backup created"
```

### Command 3.3 — Health endpoints

```bash
curl -fsS http://localhost:8000/api/health/live
curl -fsS http://localhost:8000/api/health/ready
# Expected: 200 OK on both
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 / 1.4 / 1.5 / 1.6 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 / 2.6 / 2.7 / 2.8 green
- ✅ Command 3.1 / 3.2 / 3.3 no regression
