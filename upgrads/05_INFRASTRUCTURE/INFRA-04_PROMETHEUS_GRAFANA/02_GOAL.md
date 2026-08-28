# INFRA-04: Goal and Plan

## SMART Goal

> Within **1 week (5 working days)**, complete the monitoring stack: scrape
> `api`, `worker`, `beat`, `db`, `redis`, `nginx`, `blackbox`; add alert
> rules for `database`, `celery`, `business`; add dashboards for the same;
> wire **email + Slack** notifications; add **5 runbooks**; verify the
> stack under a synthetic outage.

## Detailed Acceptance Standards

### Standard 1: Scrape matrix

| Target | Exporter | Port | Path |
|---|---|---|---|
| api | built-in | 8000 | `/api/metrics` |
| worker | celery-exporter | 9808 | `/metrics` |
| beat | celery-exporter | 9808 | `/metrics` |
| db | postgres_exporter | 9187 | `/metrics` |
| redis | redis_exporter | 9121 | `/metrics` |
| nginx | nginx_exporter | 9113 | `/metrics` |
| blackbox | blackbox_exporter | 9115 | `/probe` |

### Standard 2: Alert rules

| File | Alerts |
|---|---|
| `api.yml` | APIHighP95, API5xx, APIRateLimit, HealthCheckFailing |
| `database.yml` | DatabaseConnectionsHigh, DatabaseConnectionsExhausted, ReplicationLag, DiskSpaceLow |
| `celery.yml` | CeleryQueueDepthHigh, CeleryWorkerDown, CeleryTaskDurationHigh |
| `business.yml` | BackupLastRunOld, AuditChainDiverged, LoginFailuresHigh, EvidenceUploadLatencyHigh |

Each alert has `for:` (sustained), `severity` (critical / warning), and a `runbook_url`.

### Standard 3: Dashboards

| File | Panels |
|---|---|
| `api.json` | p50/p95/p99 latency, 4xx/5xx rate, RPS, /api/health/ready status |
| `database.json` | connections, replication lag, slow queries, vacuum, disk |
| `business.json` | daily logins, evidence uploads, review decisions, audit chain |
| `celery.json` | queue depth, task duration, worker count, success/failure rate |

### Standard 4: Alertmanager

```yaml
route:
  receiver: default
  group_by: [alertname, severity]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match: { severity: critical }
      receiver: pagerduty
    - match: { severity: warning }
      receiver: slack
receivers:
  - name: default
  - name: slack
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_URL}
        channel: "#alerts"
        send_resolved: true
  - name: pagerduty
    pagerduty_configs:
      - routing_key: ${PAGERDUTY_ROUTING_KEY}
```

### Standard 5: Runbooks

Each top-5 alert has a `docs/runbooks/<alert>.md` with:

- **What it means** (1 paragraph)
- **Triage** (5 commands to run)
- **Mitigation** (5 commands to apply)
- **Escalation** (who to call)

### Standard 6: Synthetic outage drill

| Scenario | Action | Expected alert |
|---|---|---|
| API down | `docker compose stop api` | `APIHealthCheckFailing` within 5 min |
| DB connections exhausted | saturate with 200 idle sessions | `DatabaseConnectionsExhausted` within 5 min |
| Redis memory > 90% | fill the cache | `RedisMemoryHigh` within 5 min |
| Celery worker down | `docker compose stop worker` | `CeleryWorkerDown` within 1 min |
| Audit chain diverged | mutate a row out-of-band | `AuditChainDiverged` within 1 min |

---

## Detailed Implementation Plan

### Day 1 — Scrapes + exporters

- [ ] Add `prometheus.yml` scrapes for worker, beat, db-exporter, redis-exporter, nginx-exporter, blackbox-exporter.
- [ ] Add `postgres-exporter`, `redis-exporter`, `nginx-exporter`, `celery-exporter` to `compose.monitoring.yml`.
- [ ] Confirm every exporter port is bound to `127.0.0.1`.

### Day 2 — Alert rules

- [ ] Write `database.yml`, `celery.yml`, `business.yml`.
- [ ] Add `runbook_url` to every alert.
- [ ] Run `promtool check rules` on each file.

### Day 3 — Dashboards

- [ ] Import the three missing dashboards as JSON.
- [ ] Place them in `infra/monitoring/grafana/dashboards/`.
- [ ] Add a provisioning entry in `grafana/provisioning/dashboards/`.

### Day 4 — Alertmanager + runbooks

- [ ] Wire email + Slack + PagerDuty.
- [ ] Write 5 runbooks.
- [ ] Document `SLACK_WEBHOOK_URL` and `PAGERDUTY_ROUTING_KEY` in `docs/SECRET_MANAGEMENT.md`.

### Day 5 — Verify + docs

- [ ] Boot the stack under `--profile monitoring`.
- [ ] Run a synthetic outage drill.
- [ ] Confirm alerts fire within 5 min.
- [ ] Update `docs/SERVER_INVENTORY.md` and `CHANGELOG.md`.

---

## Dependency Graph

```
exporters (Day 1)
    ↓
scrape configs (Day 1)
    ↓
alert rules (Day 2)
    ↓
dashboards (Day 3)
    ↓
Alertmanager + runbooks (Day 4)
    ↓
synthetic drill (Day 5)
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | All exporters up; targets healthy | DevOps |
| CP-2 | Alert rules load; `promtool check rules` clean | DevOps |
| CP-3 | Dashboards auto-provisioned | DevOps |
| CP-4 | Alertmanager wired | DevOps |
| CP-5 | 5 runbooks merged | DevOps |
| CP-6 | Synthetic drill fires alerts | DevOps |
| CP-7 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If a scrape fails for an exporter we cannot deploy → add a stub exporter that returns synthetic metrics; do not silently drop the scrape.
- If an alert fires constantly → fix the threshold or the SLO; do not silence the alert.
- If the dashboard takes > 5s to load → split it into smaller panels; the monitoring stack must not slow down operators.
