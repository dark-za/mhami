# Production Readiness Checklist

This document establishes the operational checklist for deploying and running Mhami in production environments.

## Checklist Categories

### 🔴 BLOCKER (Mandatory before going live)
- [ ] **Database Connection Pooling**: Ensure `psycopg_pool` is active and database connections are properly sized for expected concurrency.
- [ ] **Redis Authentication**: All Redis connections (broker, backend, cache) must be authenticated using high-entropy `REDIS_PASSWORD`.
- [ ] **HTTPS & Security Headers**: HSTS, secure cookies (`SESSION_COOKIE_SECURE=True`), and Content Security Policy enabled via reverse proxy (e.g. Nginx/Cloudflare).
- [ ] **Secret Management**: Verify `SECRET_KEY`, `BACKUP_ENCRYPTION_KEY`, and database credentials are set via secure environment variables and not checked into source control.
- [ ] **Database Backups**: Verify automated daily backups are scheduled and test backup restoration using `apps.backups.tasks.run_backup_run`.

### 🟠 REQUIRED (Necessary for reliable operations)
- [ ] **Celery Workers & Queues**: Verify `worker` and `beat` processes are running with appropriate queues (`default`, `media`, `ai`, `high_priority`).
- [ ] **Rate Limiting**: Ensure API throttling is active for authentication, backup, and export endpoints.
- [ ] **Outbox Event Processing**: Verify `process_outbox_events` is scheduled and successfully delivering notifications.
- [ ] **File Quarantining & Virus Scanning**: Ensure upload quarantine directory permissions are locked down and `python-magic` MIME validation is enforced.

### 🟡 RECOMMENDED (Operational excellence & monitoring)
- [ ] **Prometheus Metrics**: Expose `/metrics/` with authenticated `METRICS_TOKEN` to monitor request latency and worker queue depths.
- [ ] **Log Aggregation**: Collect structured JSON logs from `api`, `worker`, and `beat` to central monitoring.
- [ ] **Regular Disaster Recovery Drills**: Test offsite backup sync to external S3/MinIO bucket.
