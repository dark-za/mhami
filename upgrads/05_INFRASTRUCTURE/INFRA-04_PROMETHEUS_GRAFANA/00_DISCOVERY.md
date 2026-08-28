# INFRA-04: Prometheus / Grafana / Alertmanager

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The platform has a **partial** monitoring stack: `infra/monitoring/compose.monitoring.yml` defines `prometheus`, `alertmanager`, `grafana`, and `blackbox-exporter` behind a `--profile monitoring`. The Prometheus config is a single scrape of `api:8000/api/metrics` with a bearer token. There is **no alert rules file**, no `business.json` dashboard, no `database.yml` or `celery.yml` alerts, and no scrape of `worker` / `beat` / `db` / `redis`. Gate-D requires the full set.

**Evidence gathered:**
- `infra/monitoring/prometheus.yml` — single scrape of `api:8000`.
- `infra/monitoring/alertmanager/alertmanager.yml` — file exists.
- `infra/monitoring/grafana/dashboards/` — `api.json` exists; `database.json`, `business.json`, `celery.json` are absent.
- `infra/monitoring/prometheus/alerts/` — `api.yml` exists; `database.yml`, `celery.yml` are absent.
- `infra/monitoring/compose.monitoring.yml` — services are present but behind a profile, so they do not boot by default.

### Impact

| Dimension | Impact |
|---|---|
| Functional | No visibility into database, redis, or celery. |
| Operational | No alert on backup failure, audit-chain divergence, or queue depth. |
| Compliance | Gate-D requires evidence of monitoring; the current setup is incomplete. |
| Financial | Late incident detection is more expensive. |

### Reproducible Evidence

```bash
# 1. Confirm partial coverage
Get-ChildItem infra\monitoring\prometheus\alerts
# Expected today: api.yml only

Get-ChildItem infra\monitoring\grafana\dashboards
# Expected today: api.json only

# 2. Confirm worker / beat / db / redis are not scraped
Select-String -Path infra\monitoring\prometheus\prometheus.yml -Pattern "worker|beat|db|redis"
# Expected today: 0 matches

# 3. Confirm alert rules
Select-String -Path infra\monitoring\prometheus\alerts\*.yml -Pattern "alert:"
# Expected today: only in api.yml
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Scrape targets | api only | api, worker, beat, db (postgres_exporter), redis (redis_exporter), nginx (nginx_exporter), blackbox |
| Alert rules | api.yml | api.yml + database.yml + celery.yml + business.yml |
| Dashboards | api.json | api.json + database.json + business.json + celery.json |
| SLOs | none | latency, error rate, throughput, queue depth, audit-chain, backup last run |
| Notification channels | none | email + Slack + PagerDuty (rotated) |
| Runbooks | none | `docs/runbooks/` per alert |

---

## 3. Goal Statement

> Within **1 week (5 working days)**, complete the monitoring stack: scrape `api`, `worker`, `beat`, `db`, `redis`, `nginx`; add alert rules for `database.yml`, `celery.yml`, `business.yml`; add dashboards for `database.json`, `business.json`, `celery.json`; wire **email + Slack** notification channels; add **runbooks** for the top 5 alerts; verify the stack under a synthetic load.

### Acceptance Criteria

1. **AC-1:** `prometheus.yml` scrapes `api`, `worker`, `beat`, `db-exporter`, `redis-exporter`, `nginx-exporter`, and `blackbox-exporter`.
2. **AC-2:** Alert rules exist for `database.yml`, `celery.yml`, `business.yml` and they fire on a synthetic outage.
3. **AC-3:** Dashboards exist for `database.json`, `business.json`, `celery.json` and are auto-provisioned.
4. **AC-4:** Alertmanager is wired to email and Slack.
5. **AC-5:** Runbooks exist for the top 5 alerts (API p95, DB connections, Redis memory, Celery queue, audit-chain).
6. **AC-6:** The stack is brought up under `--profile monitoring` and every dashboard loads.
7. **AC-7:** A `k6` outage scenario causes an alert to fire within 5 minutes.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Prometheus storage grows unbounded | Medium | High | `retention.time=30d` (already set); add a remote write to a long-term store. |
| Alertmanager loses its state on restart | Medium | High | Use a persistent volume (already mounted). |
| Slack webhook leaks | Low | High | Store in `SLACK_WEBHOOK_URL` secret, never in compose plain text. |
| Exporter ports exposed to the public | High | High | Bind to `127.0.0.1` only (already done in compose). |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `prometheus.yml` scrapes for worker, beat, db-exporter, redis-exporter, nginx-exporter | DevOps | not-started |
| 2 | Add `postgres-exporter` and `redis-exporter` services to `compose.monitoring.yml` | DevOps | not-started |
| 3 | Add `database.yml`, `celery.yml`, `business.yml` alert rules | DevOps | not-started |
| 4 | Add `database.json`, `business.json`, `celery.json` dashboards | DevOps | not-started |
| 5 | Configure Alertmanager (email + Slack) | DevOps | not-started |
| 6 | Write runbooks in `docs/runbooks/` | DevOps | not-started |
| 7 | Add `monitoring` profile smoke test | DevOps | not-started |
| 8 | Update `docs/SERVER_INVENTORY.md` and `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [infra/monitoring/](../../../infra/monitoring/) — existing config
- [infra/monitoring/compose.monitoring.yml](../../../infra/monitoring/compose.monitoring.yml)
- [docs/SERVER_INVENTORY.md](../../../docs/SERVER_INVENTORY.md) — SLOs
- [QA-04 — k6 Performance](..) — synthetic load for alert verification
