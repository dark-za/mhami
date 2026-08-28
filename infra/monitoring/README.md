# Monitoring Assets

Health and alerting assets for the platform.

## Health endpoints (exposed by the API, no auth)

- `GET /api/health/live` -> `{"status": "ok"}` (liveness)
- `GET /api/health/ready` -> `{"status": "ok", "database": "ok", "redis": "ok"}`
  (readiness; `database`/`redis` are per-dependency, overall state is
  `ok`/`degraded`)
- `GET /api/v1/health/modules` -> per-module health report
- `GET /api/v1/status` -> module health + metrics report with `ai`, `connector`,
  `exports`, and `backups` JSON counters

`GET /api/v1/metrics` is a token-protected Prometheus text endpoint. It reports
database and Redis reachability, Celery worker count and queue depth
(`default`, `media`, `ai`), media-volume capacity, and the timestamps of the
latest successful and failed backup attempts. Scrape it as `job="platform-api"`
with the `X-Metrics-Token` header. Keep that token in the production secret
store and do not publish the endpoint through the public edge.

## alert-rules.yml

Prometheus/Alertmanager rules. The rules use Blackbox-exporter HTTP/TCP probes
for API, PostgreSQL, and Redis, plus the API metrics endpoint for worker
availability, queue backlog, media-disk capacity, and backup freshness/failure.
The backup freshness alert allows a two-hour operational grace period over the
24-hour RPO.

## Validation limits

Alertmanager and Blackbox exporter are not bundled into the application stack;
their scrape targets, receivers, and escalation policy must be configured by
the production operator. Validate rule syntax and target labels at deployment
time.