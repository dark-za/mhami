# INFRA-04: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. The monitoring stack is **opt-in** via `--profile monitoring`; production runs it permanently.

## Step 1: Add exporters to `compose.monitoring.yml`

### 1.1 File before

```yaml
services:
  prometheus:
    ...
  alertmanager:
    ...
  grafana:
    ...
  blackbox-exporter:
    ...
```

### 1.2 File after

```yaml
services:
  prometheus:
    ...
  alertmanager:
    ...
  grafana:
    ...
  blackbox-exporter:
    ...

  postgres-exporter:
    image: prom/postgres-exporter:v0.15.0
    user: "65534:65534"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    pids_limit: 50
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}?sslmode=disable"
    ports:
      - "127.0.0.1:9187:9187"
    profiles: [monitoring]

  redis-exporter:
    image: oliver006/redis_exporter:v1.62.0
    user: "65534:65534"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    pids_limit: 50
    restart: unless-stopped
    environment:
      REDIS_ADDR: "redis://redis:6379"
    ports:
      - "127.0.0.1:9121:9121"
    profiles: [monitoring]

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:1.4.0
    user: "65534:65534"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 64m
    pids_limit: 50
    restart: unless-stopped
    command:
      - --nginx.scrape-uri=http://nginx/stub_status
    ports:
      - "127.0.0.1:9113:9113"
    profiles: [monitoring]

  celery-exporter:
    image: mher/celery-exporter:0.7
    user: "65534:65534"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    pids_limit: 50
    restart: unless-stopped
    environment:
      CELERY_BROKER_URL: "redis://redis:6379/0"
      CELERY_RESULT_BACKEND: "redis://redis:6379/0"
    ports:
      - "127.0.0.1:9808:9808"
    profiles: [monitoring]
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring config --services | Sort-Object
# Expected: alertmanager, blackbox-exporter, celery-exporter, grafana, nginx-exporter, postgres-exporter, prometheus, redis-exporter
```

---

## Step 2: Update `prometheus.yml`

### 2.1 File before — `infra/monitoring/prometheus/prometheus.yml`

```yaml
scrape_configs:
  - job_name: mhami-backend
    metrics_path: /api/metrics
    scheme: https
    static_configs:
      - targets: [api:8000]
    authorization:
      type: Bearer
      credentials_file: /etc/prometheus/metrics_token
```

### 2.2 File after

```yaml
scrape_configs:
  - job_name: mhami-backend
    metrics_path: /api/metrics
    scheme: https
    static_configs:
      - targets: [api:8000]
    authorization:
      type: Bearer
      credentials_file: /etc/prometheus/metrics_token

  - job_name: celery
    static_configs:
      - targets: [celery-exporter:9808]

  - job_name: postgres
    static_configs:
      - targets: [postgres-exporter:9187]

  - job_name: redis
    static_configs:
      - targets: [redis-exporter:9121]

  - job_name: nginx
    static_configs:
      - targets: [nginx-exporter:9113]

  - job_name: blackbox
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - http://api:8000/api/health/live
          - http://nginx:8080/healthz
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

rule_files:
  - /etc/prometheus/alerts/*.yml
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring exec prometheus promtool check config /etc/prometheus/prometheus.yml
# Expected: "SUCCESS"
```

---

## Step 3: Alert rules

### 3.1 `infra/monitoring/prometheus/alerts/database.yml`

```yaml
groups:
  - name: database
    rules:
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Postgres connections > 80 ({{ $value }})"
          runbook_url: "https://runbooks.example.com/db-connections-high"

      - alert: DatabaseConnectionsExhausted
        expr: pg_stat_activity_count >= pg_settings_max_connections - 5
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "Postgres near max connections"
          runbook_url: "https://runbooks.example.com/db-connections-exhausted"

      - alert: ReplicationLag
        expr: pg_replication_lag_seconds > 30
        for: 2m
        labels: { severity: warning }
        annotations:
          summary: "Replication lag {{ $value }}s"
          runbook_url: "https://runbooks.example.com/replication-lag"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/var/lib/postgresql"} / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "DB disk < 10% free"
          runbook_url: "https://runbooks.example.com/disk-space-low"
```

### 3.2 `infra/monitoring/prometheus/alerts/celery.yml`

```yaml
groups:
  - name: celery
    rules:
      - alert: CeleryQueueDepthHigh
        expr: celery_queue_length > 1000
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Queue {{ $labels.queue }} depth {{ $value }}"
          runbook_url: "https://runbooks.example.com/celery-queue"

      - alert: CeleryWorkerDown
        expr: up{job="celery"} == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "Celery worker is down"
          runbook_url: "https://runbooks.example.com/celery-worker"

      - alert: CeleryTaskDurationHigh
        expr: celery_task_runtime_seconds > 60
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Task {{ $labels.task }} p95 > 60s"
          runbook_url: "https://runbooks.example.com/celery-task-duration"
```

### 3.3 `infra/monitoring/prometheus/alerts/business.yml`

```yaml
groups:
  - name: business
    rules:
      - alert: BackupLastRunOld
        expr: time() - mhami_backup_last_run_timestamp_seconds > 86400
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Backup has not run in 24h"
          runbook_url: "https://runbooks.example.com/backup-stale"

      - alert: AuditChainDiverged
        expr: mhami_audit_chain_ok == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "Audit chain diverged"
          runbook_url: "https://runbooks.example.com/audit-chain"

      - alert: LoginFailuresHigh
        expr: rate(mhami_login_failures_total[5m]) > 5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Login failure rate > 5/s"
          runbook_url: "https://runbooks.example.com/login-failures"

      - alert: EvidenceUploadLatencyHigh
        expr: histogram_quantile(0.95, rate(mhami_evidence_upload_seconds_bucket[5m])) > 5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Evidence upload p95 > 5s"
          runbook_url: "https://runbooks.example.com/evidence-upload-latency"
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring exec prometheus promtool check rules /etc/prometheus/alerts/database.yml /etc/prometheus/alerts/celery.yml /etc/prometheus/alerts/business.yml
# Expected: "SUCCESS" for each file
```

---

## Step 4: Alertmanager wiring

### 4.1 File before — `infra/monitoring/alertmanager/alertmanager.yml`

```yaml
# existing minimal config
```

### 4.2 File after

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: default
  group_by: [alertname, severity]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match: { severity: critical }
      receiver: pagerduty
      continue: true
    - match: { severity: warning }
      receiver: slack

receivers:
  - name: default
    email_configs:
      - to: oncall@example.com
        from: alerts@example.com
        smarthost: smtp.example.com:587
        auth_username: ${SMTP_USERNAME}
        auth_password: ${SMTP_PASSWORD}
        headers:
          Subject: '[mhami] {{ .GroupLabels.alertname }}'

  - name: slack
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_URL}
        channel: "#alerts"
        send_resolved: true
        title: '{{ .GroupLabels.alertname }} ({{ .GroupLabels.severity }})'
        text: |
          {{ range .Alerts }}{{ .Annotations.summary }}
          {{ .Annotations.runbook_url }}
          {{ end }}

  - name: pagerduty
    pagerduty_configs:
      - routing_key: ${PAGERDUTY_ROUTING_KEY}
        send_resolved: true
```

**Verify:**
```bash
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
# Expected: "found valid configuration"
```

---

## Step 5: Dashboards

### 5.1 Provisioning

`infra/monitoring/grafana/provisioning/dashboards/mhami.yml`:

```yaml
apiVersion: 1
providers:
  - name: mhami
    orgId: 1
    folder: Mhami
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: false
```

### 5.2 Dashboards

Place `database.json`, `business.json`, `celery.json` in `infra/monitoring/grafana/dashboards/`. The structure mirrors `api.json`:

```json
{
  "title": "Mhami / Database",
  "uid": "mhami-database",
  "schemaVersion": 39,
  "version": 1,
  "refresh": "30s",
  "time": { "from": "now-6h", "to": "now" },
  "panels": [
    { "type": "stat", "title": "Connections", "targets": [{ "expr": "pg_stat_activity_count" }] },
    { "type": "graph", "title": "Connections (5m)", "targets": [{ "expr": "pg_stat_activity_count" }] },
    { "type": "stat", "title": "Replication lag", "targets": [{ "expr": "pg_replication_lag_seconds" }] },
    { "type": "graph", "title": "Slow queries", "targets": [{ "expr": "rate(pg_stat_activity_max_tx_duration[5m])" }] }
  ]
}
```

**Verify:**
```bash
curl -fsS -u admin:$GRAFANA_ADMIN_PASSWORD http://localhost:3000/api/search?type=dash-db | jq 'length'
# Expected: ≥4
```

---

## Step 6: Runbooks

### 6.1 `docs/runbooks/api-p95.md`

```markdown
# API p95 > 500ms

## What it means
The 95th percentile of API request duration exceeded 500ms for 5m.

## Triage
1. `kubectl logs -l app=api --tail=200 | grep -i "timeout\|slow"`
2. `curl -fsS http://api:8000/api/metrics | grep http_request_duration`
3. `docker compose exec db psql -c "SELECT pid, state, query FROM pg_stat_activity ORDER BY xact_start LIMIT 20"`
4. `docker compose exec redis redis-cli INFO memory`
5. `kubectl top pod -l app=api`

## Mitigation
- Scale api replicas: `kubectl scale deploy api --replicas=6`.
- Restart the slowest worker: `kubectl delete pod -l app=worker --field-selector=status.phase=Running`.
- Add a missing index (after review): see DBA runbook.

## Escalation
- Backend Lead (oncall).
- DBA (if queries are slow).
- Platform Owner (if user impact > 5 min).
```

> Repeat for `db-connections-high.md`, `redis-memory-high.md`, `celery-queue-depth.md`, `audit-chain-diverged.md`.

---

## Step 7: Synthetic outage drill

### 7.1 `scripts/dev/synthetic-outage.sh`

```bash
#!/usr/bin/env bash
# Boot the monitoring stack, fire 5 synthetic alerts, and confirm Alertmanager.

set -euo pipefail

docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring up -d

echo "Waiting for Prometheus targets..."
for i in $(seq 1 30); do
  targets=$(curl -fsS http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length')
  if [ "$targets" -ge 5 ]; then break; fi
  sleep 2
done

echo "Stopping api to fire APIHealthCheckFailing..."
docker compose -f compose.yml -f compose.prod.yml stop api

echo "Sleeping 5 min for the alert to fire..."
sleep 300

echo "Alerts:"
curl -fsS http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alert: .labels.alertname, severity: .labels.severity, state: .state}'

docker compose -f compose.yml -f compose.prod.yml up -d api
```

**Verify:**
```bash
bash scripts/dev/synthetic-outage.sh
echo "Exit code: $LASTEXITCODE"
# Expected: 0; jq output lists ≥1 alert
```

---

## Step 8: Documentation

1. Update `docs/SERVER_INVENTORY.md` with the monitoring SLOs.
2. Update `docs/SECRET_MANAGEMENT.md` with `SLACK_WEBHOOK_URL`, `PAGERDUTY_ROUTING_KEY`, `SMTP_USERNAME`, `SMTP_PASSWORD`.
3. Update `CHANGELOG.md` with an `INFRA-04` entry.
4. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| All exporters up | `docker compose ... --profile monitoring ps` | all Up |
| Targets healthy | `curl http://localhost:9090/api/v1/targets` | all "up" |
| Rules loaded | `curl http://localhost:9090/api/v1/rules` | 4+ groups |
| Alertmanager config | `amtool check-config` | ok |
| Dashboards | `curl http://localhost:3000/api/search` | ≥4 |
| Runbooks | `Get-ChildItem docs\runbooks` | ≥5 |
| Public ports | none | only 127.0.0.1:* |

---

## Rollback

```bash
git revert <infra04-commit-sha>
docker compose -f compose.yml -f compose.prod.yml -f infra/monitoring/compose.monitoring.yml --profile monitoring down
```
