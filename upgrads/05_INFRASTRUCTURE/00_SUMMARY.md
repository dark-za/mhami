# Section 5: Infrastructure

## List of Fixes

| # | Title | Priority | Duration |
|---|---|---|---|
| INFRA-01 | Hardened production Compose | P0 | 1 week |
| INFRA-02 | Content-Security-Policy | P0 | 2 days |
| INFRA-03 | Upload backups to S3 | P1 | 1 week |
| INFRA-04 | Prometheus/Grafana | P1 | 1 week |
| INFRA-05 | Let's Encrypt | P1 | 3 days |

## INFRA-01: Hardened Production Compose (Detail)

### Status
- `compose.yml` and `compose.prod.yml` have gaps (see C-02).

### Fixes
1. Add `AUDIT_HMAC_SECRET` as mandatory.
2. Remove `:-change-me` defaults.
3. Add `read_only: true` on `/etc/passwd` (added for hardening).
4. `cap_drop: [ALL]` + `cap_add: [NET_BIND_SERVICE]` only.
5. `user: "1000:1000"` instead of root.
6. `security_opt: [no-new-privileges:true]`.
7. `pids_limit: 100`.
8. `mem_limit: 512m` for every service.

### Form
```yaml
services:
  api:
    build:
      context: ./backend
    user: "1000:1000"
    read_only: true
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt:
      - no-new-privileges:true
    pids_limit: 100
    mem_limit: 512m
    tmpfs:
      - /tmp:size=50M
    volumes:
      - media-data:/app/media:rw
      - static-data:/app/staticfiles:ro
    environment:
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
      AUDIT_HMAC_SECRET: ${AUDIT_HMAC_SECRET:?Set AUDIT_HMAC_SECRET in .env}
      # ... all mandatory
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/api/health/ready"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## INFRA-02: Content-Security-Policy (Detail)

### Status
- `infra/nginx/security-headers.conf` does not contain CSP.

### Required rollout

Do not deploy a literal `nonce-{NONCE}` value from NGINX. A nonce must be the
same random value in both the response header and an inline HTML element; the
static SPA currently does not establish that contract. Start with
`Content-Security-Policy-Report-Only`, collect reviewed violation reports for
7-14 days, then enforce a static policy such as `script-src 'self'` unless an
actual inline-script use case requires a server-owned nonce.

### Illustrative policy only
```nginx
# infra/nginx/security-headers.conf
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "same-origin" always;
add_header Permissions-Policy "geolocation=(), camera=(), microphone=()" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Content-Security-Policy "
  default-src 'self';
  script-src 'self' 'nonce-{NONCE}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob:;
  font-src 'self';
  connect-src 'self';
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
  upgrade-insecure-requests;
" always;
```

### Nonce generation
```python
# middleware
class CSPNonceMiddleware:
    def __call__(self, request):
        nonce = secrets.token_urlsafe(16)
        request.csp_nonce = nonce
        response = self.get_response(request)
        return response
```

The middleware example is incomplete unless it writes the nonce to the actual
CSP header and the rendered HTML. Do not add it to a static NGINX-served SPA
without that end-to-end design and browser tests.

## INFRA-03: Backup to S3 (Detail)

### Status
- `BACKUP_EXTERNAL_URI` is defined but not used.

### Required design constraints

The implementation must not write a plaintext archive and then treat a
single environment Fernet key as production encryption. It needs a versioned
artifact format, AEAD/envelope encryption with `key_id`, key rotation,
restricted temporary storage, remote checksum verification, upload retry state,
and a restore-from-external drill. S3 upload must use least-privilege IAM,
SSE-KMS, versioning/lifecycle, and an approved object-retention policy.

### Illustrative upload only
```python
# apps/backups/services.py
def upload_to_external(artifact_path: Path, company: Company):
    uri = settings.BACKUP_EXTERNAL_URI  # s3://bucket/path
    if uri.startswith("s3://"):
        import boto3
        s3 = boto3.client("s3")
        bucket, key = parse_s3_uri(uri)
        s3.upload_file(
            str(artifact_path),
            bucket,
            f"{key}/{company.code}/{artifact_path.name}",
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "Metadata": {
                    "company_id": str(company.id),
                    "sha256": _sha256(artifact_path.read_bytes()),
                },
            },
        )
    elif uri.startswith("azure://"):
        # ... Azure implementation
```

### Retention
- 30 days for daily backups
- 90 days for weekly backups
- 1 year for monthly backups

## INFRA-04: Prometheus/Grafana (Detail)

### Structure
```
infra/monitoring/
├── prometheus/
│   ├── prometheus.yml
│   ├── alerts/
│   │   ├── api.yml
│   │   ├── database.yml
│   │   └── celery.yml
├── grafana/
│   ├── dashboards/
│   │   ├── api.json
│   │   ├── database.json
│   │   └── business.json
└── alertmanager/
    └── alertmanager.yml
```

### Critical metrics
- API response time (p50, p95, p99)
- API error rate (4xx, 5xx)
- DB connections active
- Redis memory
- Celery queue depth
- Backup last run
- Audit chain integrity

## INFRA-05: Let's Encrypt (Detail)

### certbot container
```yaml
certbot:
  image: certbot/certbot
  volumes:
    - certs:/etc/letsencrypt
    - certbot-webroot:/var/www/certbot
  command: certonly --webroot --webroot-path=/var/www/certbot --email admin@example.com --agree-tos --no-eff-email -d api.example.com
```

### Renewal cron
```yaml
certbot-renew:
  image: certbot/certbot
  restart: unless-stopped
  command: >
    sh -c "trap exit TERM;
    while :; do
      certbot renew;
      sleep 12h;
    done"
```

The final Compose design must prove certificate bootstrap before NGINX binds
443, renewal reload behavior, redirect of all HTTP paths including `/api/`, and
an HTTPS smoke test using a non-production certificate in CI.
