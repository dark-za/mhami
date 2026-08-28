# INFRA-04: Verification Commands

> **Instructions:** Run baseline (Phase 1) before the change, then post-fix (Phase 2) to confirm the full monitoring stack is up and alerting.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Partial alerts / dashboards

```bash
Get-ChildItem infra\monitoring\prometheus\alerts
# Expected: api.yml only
Get-ChildItem infra\monitoring\grafana\dashboards
# Expected: api.json only
```

### Command 1.2 — Single scrape

```bash
Select-String -Path infra\monitoring\prometheus\prometheus.yml -Pattern "targets"
# Expected: 1 line (api)
```

### Command 1.3 — No runbooks

```bash
Get-ChildItem docs\runbooks -ErrorAction SilentlyContinue
# Expected: empty
```

### Command 1.4 — Alertmanager not wired

```bash
Select-String -Path infra\monitoring\alertmanager\alertmanager.yml -Pattern "slack|email"
# Expected: 0 matches
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — Multi-target scrape

```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring up -d
curl -fsS http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Expected: ≥5 (api, worker, beat, db-exporter, redis-exporter, nginx-exporter, blackbox-exporter)
```

### Command 2.2 — Alert rules loaded

```bash
curl -fsS http://localhost:9090/api/v1/rules | jq '.data.groups | length'
# Expected: ≥4 (api, database, celery, business)
```

### Command 2.3 — Dashboards provisioned

```bash
curl -fsS -u admin:$GRAFANA_ADMIN_PASSWORD http://localhost:3000/api/search?type=dash-db | jq 'length'
# Expected: ≥4 (api, database, business, celery)
```

### Command 2.4 — Alertmanager wired

```bash
curl -fsS http://localhost:9093/api/v2/receivers | jq '.[].name'
# Expected: email + slack (or equivalent)
```

### Command 2.5 — Synthetic outage fires an alert

```bash
# Stop the API and wait 5 minutes
docker compose -f compose.yml -f compose.prod.yml stop api
sleep 300
curl -fsS http://localhost:9090/api/v1/alerts | jq '.data.alerts | length'
# Expected: ≥1 (API down)

# Restore
docker compose -f compose.yml -f compose.prod.yml up -d api
```

### Command 2.6 — Runbooks exist

```bash
Get-ChildItem docs\runbooks -Filter "*.md"
# Expected: ≥5 files
```

### Command 2.7 — Stack survives a restart

```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring restart prometheus alertmanager grafana
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring ps
# Expected: all Up (healthy) within 30s
```

### Command 2.8 — No public ports

```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring ps --format json | jq '.[] | select(.Publishers | length > 0) | {Service: .Name, Ports: .Publishers[].PublishedPort}'
# Expected: only 127.0.0.1:* ports
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Existing services still boot

```bash
docker compose -f compose.yml -f compose.prod.yml up -d
docker compose -f compose.yml -f compose.prod.yml ps
# Expected: all Up (healthy)
```

### Command 3.2 — Audit chain still healthy

```bash
docker compose -f compose.yml exec backend python manage.py shell -c "
from apps.audit.services import verify_chain
print(verify_chain())
"
# Expected: True
```

### Command 3.3 — Metrics endpoint not publicly exposed

```bash
curl -fsS http://api:8000/api/metrics
echo "Exit code: $LASTEXITCODE"
# Expected: 401 (bearer token required)
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 / 1.4 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 / 2.6 / 2.7 / 2.8 green
- ✅ Command 3.1 / 3.2 / 3.3 no regression
