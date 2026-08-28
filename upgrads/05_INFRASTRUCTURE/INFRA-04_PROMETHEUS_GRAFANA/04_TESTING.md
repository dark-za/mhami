# INFRA-04: Test Strategy

> **Rule:** every check in this file must run against a real `--profile monitoring` stack. The **synthetic outage drill** is the gate.

## 1. Unit Tests

Not applicable — INFRA-04 is a deployment-config change.

## 2. Integration Tests

### 2.1 `promtool check config`

```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring exec prometheus promtool check config /etc/prometheus/prometheus.yml
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### 2.2 `promtool check rules`

```bash
docker compose ... exec prometheus promtool check rules /etc/prometheus/alerts/*.yml
echo "Exit code: $LASTEXITCODE"
# Expected: 0 for each file
```

### 2.3 `amtool check-config`

```bash
docker compose ... exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## 3. End-to-End Tests

### 3.1 Targets up

```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring up -d
curl -fsS http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
# Expected: 7+ rows, all "up"
```

### 3.2 Rules loaded

```bash
curl -fsS http://localhost:9090/api/v1/rules | jq '.data.groups[] | .name'
# Expected: api, database, celery, business
```

### 3.3 Dashboards provisioned

```bash
curl -fsS -u admin:$GRAFANA_ADMIN_PASSWORD http://localhost:3000/api/search?type=dash-db | jq '.[].title'
# Expected: Mhami / API, Mhami / Database, Mhami / Celery, Mhami / Business
```

### 3.4 Synthetic API outage

```bash
docker compose -f compose.yml -f compose.prod.yml stop api
sleep 300
curl -fsS http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname | test("API|Health")) | .labels.alertname'
# Expected: ≥1 alert
docker compose -f compose.yml -f compose.prod.yml up -d api
```

### 3.5 Synthetic DB connection saturation

```bash
docker compose -f compose.yml -f compose.prod.yml exec db psql -c "SELECT pg_sleep(0);" &
for i in $(seq 1 180); do
  docker compose -f compose.yml -f compose.prod.yml exec db psql -c "SELECT 1" >/dev/null &
done
sleep 300
curl -fsS http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname == "DatabaseConnectionsHigh")'
# Expected: ≥1 alert
```

### 3.6 Synthetic Celery worker down

```bash
docker compose -f compose.yml -f compose.prod.yml stop worker
sleep 120
curl -fsS http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname == "CeleryWorkerDown")'
# Expected: ≥1 alert
docker compose -f compose.yml -f compose.prod.yml up -d worker
```

### 3.7 No public ports

```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring ps --format json | jq '.[] | .Publishers[]? | select(.PublishedPort != null) | {Service: .Service, PublishedPort, TargetPort}'
# Expected: all PublishedPort = 127.0.0.1:*
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| `promtool check config` | 1 | exit 0 |
| `promtool check rules` | 3+ | exit 0 |
| `amtool check-config` | 1 | exit 0 |
| Targets up | 7+ | all "up" |
| Rules loaded | 4 | api, database, celery, business |
| Dashboards | 4 | Mhami / API, Database, Celery, Business |
| Synthetic API outage | 1 | alert fires |
| Synthetic DB saturation | 1 | alert fires |
| Synthetic Celery down | 1 | alert fires |
| No public ports | 0 | 0 rows |

---

## 5. Run Tests

### 5.1 Local

```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring up -d
docker compose ... exec prometheus promtool check config /etc/prometheus/prometheus.yml
docker compose ... exec prometheus promtool check rules /etc/prometheus/alerts/*.yml
docker compose ... exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
curl -fsS http://localhost:9090/api/v1/targets
curl -fsS -u admin:$GRAFANA_ADMIN_PASSWORD http://localhost:3000/api/search?type=dash-db
```

### 5.2 Synthetic drill

```bash
bash scripts/dev/synthetic-outage.sh
```

### 5.3 CI

The `monitoring-smoke` job in `.github/workflows/ci.yml` (add) runs `promtool` + `amtool` and boots the stack for 5 min to confirm dashboards load.

---

## 6. Failure simulation

| Scenario | Expected |
|---|---|
| Remove `rule_files` from `prometheus.yml` | rules count drops to 0; alerts are 0 |
| Stop the API | `APIHealthCheckFailing` fires within 5 min |
| Saturate DB connections | `DatabaseConnectionsHigh` fires within 5 min |
| Stop the worker | `CeleryWorkerDown` fires within 1 min |
| Bind `9090:9090` (public) | fails the `No public ports` check |

---

## 7. Cross-links

- [INFRA-01 — Hardened Compose](..) — exporters added there.
- [QA-04 — k6 Performance](..) — synthetic load used by the drill.
- [upgrads/01_CRITICAL_FIXES/C-01_BROWSER_ROUTER_NESTING](../../01_CRITICAL_FIXES/C-01_BROWSER_ROUTER_NESTING/00_DISCOVERY.md) — share the C-01 pattern.
