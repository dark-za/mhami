# INFRA-03: Goal and Plan

## SMART Goal

> Within **1 week (5 working days)**, implement an **envelope-encrypted,
> retry-with-backoff, checksum-verified** backup upload to S3 (and
> Azure / GCS adapters), with **per-artifact `key_id`**, **at-least-two
> active KEKs**, **restricted `/tmp` staging**, and a **weekly
> restore-from-external drill** that the platform owner can trigger.

## Detailed Acceptance Standards

### Standard 1: Artifact header

```json
{
  "version": 1,
  "key_id": "kek-2026-Q3",
  "ciphertext_hash": "sha256:...",
  "created_at": "2026-08-28T12:00:00Z",
  "company_id": "uuid",
  "artifact_type": "db+media",
  "compression": "zstd",
  "encryption": "AES-256-GCM",
  "kek_alg": "AES-256-GCM"
}
```

The header is the first N bytes of the artifact (length-prefixed JSON). Decryption is impossible without the header.

### Standard 2: Envelope encryption

1. Generate a **per-artifact 256-bit data key** with `cryptography.hazmat.primitives.ciphers.aead.AESGCM`.
2. Encrypt the artifact with the data key.
3. Encrypt the data key with the **active KEK** (AES-256-GCM). The KEK is identified by `key_id` in the header.
4. Keep **at least two active KEKs**: `kek-2026-Q3` (encrypt) and `kek-2026-Q2` (decrypt only). Rotation is a flag flip.

### Standard 3: `BACKUP_EXTERNAL_URI` dispatch

| Scheme | Provider |
|---|---|
| `s3://bucket[/prefix]` | AWS S3 (or MinIO for local) |
| `azure://account/container[/prefix]` | Azure Blob |
| `gs://bucket[/prefix]` | Google Cloud Storage |
| `file:///path[/prefix]` | Local FS (for tests) |

The provider is selected at runtime; no provider-specific code lives in the calling layer.

### Standard 4: Retry + circuit breaker

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type((BotoCoreError, ConnectionError, TimeoutError)),
    reraise=True,
)
def _upload_once(...): ...
```

A circuit breaker (`pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)`) wraps the call to avoid hammering S3 during a regional outage.

### Standard 5: S3 bucket policy

```hcl
resource "aws_s3_bucket" "backup" {
  bucket = "mhami-backups"
}

resource "aws_s3_bucket_versioning" "backup" {
  bucket = aws_s3_bucket.backup.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_lifecycle_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id
  rule {
    id     = "expire"
    status = "Enabled"
    transition { days = 30  storage_class = "STANDARD_IA" }
    transition { days = 90  storage_class = "GLACIER" }
    expiration { days = 365 }
  }
}

resource "aws_s3_bucket_policy" "backup" {
  bucket = aws_s3_bucket.backup.id
  policy = data.aws_iam_policy_document.backup.json
}

data "aws_iam_policy_document" "backup" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [aws_s3_bucket.backup.arn, "${aws_s3_bucket.backup.arn}/*"]
    principals { type = "*" identifiers = ["*"] }
    condition { test = "Bool" values = ["false"] variable = "aws:SecureTransport" }
  }
}
```

### Standard 6: Restore drill

```bash
docker compose -f compose.yml exec backend python manage.py drill_restore_from_external --tenant=testco
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

The command:

1. Creates a synthetic `testco` tenant.
2. Runs a backup.
3. Uploads to S3 / MinIO.
4. Deletes the local artifact.
5. Restores from S3 / MinIO.
6. Re-hashes and compares.
7. Writes a `BackupDrillReport` row to the audit log.
8. Returns 0 on success, 1 on failure.

The command **refuses** to run against any tenant whose `code` does not start with `test`.

### Standard 7: Secrets

| Name | Purpose | Storage |
|---|---|---|
| `BACKUP_S3_ACCESS_KEY_ID` | S3 access | CI / compose |
| `BACKUP_S3_SECRET_ACCESS_KEY` | S3 secret | CI / compose (never logged) |
| `BACKUP_S3_KMS_KEY_ID` | SSE-KMS key | CI / compose |
| `BACKUP_S3_ROLE_ARN` | IAM role for STS | CI / compose |
| `MFA_ENCRYPTION_KEYS` | KEKs (JSON) | CI / compose |

### Standard 8: Weekly CI

`.github/workflows/ci.yml` has a `backup-drill` job on `cron: '0 4 * * 1'` (Monday 04:00 UTC) that:

1. Boots the stack + MinIO.
2. Runs `drill_restore_from_external`.
3. Uploads the report as an artifact.

---

## Detailed Implementation Plan

### Day 1 — Envelope encryption + header

- [ ] Implement `apps.backups.services.envelope_encrypt` and `envelope_decrypt`.
- [ ] Add the artifact header (length-prefixed JSON).
- [ ] Add unit tests (`tests/test_envelope.py`).

### Day 2 — `upload_to_external` + retry

- [ ] Implement S3 / Azure / GCS adapters.
- [ ] Add `@retry` and circuit breaker.
- [ ] Add `BACKUP_S3_*` env vars to `compose.prod.yml`.

### Day 3 — `restore_from_external` + checksum

- [ ] Implement `restore_from_external(key)`.
- [ ] Re-hash and compare on download.
- [ ] Add unit + integration tests.

### Day 4 — Drill + Terraform

- [ ] Add `drill_restore_from_external` management command.
- [ ] Add Terraform for the S3 bucket (versioning, lifecycle, policy).
- [ ] Wire `backup-drill` weekly job in CI.

### Day 5 — Docs + sign-off

- [ ] Update `docs/BACKUP_RESTORE.md` with the new flow.
- [ ] Update `docs/SECRET_MANAGEMENT.md`.
- [ ] Update `CHANGELOG.md`.

---

## Dependency Graph

```
envelope encryption (Day 1)
    ↓
upload_to_external + retry (Day 2)
    ↓
restore_from_external + checksum (Day 3)
    ↓
drill + Terraform + CI (Day 4)
    ↓
docs + sign-off (Day 5)
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Envelope encryption round-trip green | Backend |
| CP-2 | Upload to S3 with SSE-KMS green | Backend |
| CP-3 | Restore from S3 + checksum green | Backend |
| CP-4 | Drill command green | Backend |
| CP-5 | Terraform applied (versioning, lifecycle, policy) | DevOps |
| CP-6 | Weekly CI job green | DevOps |
| CP-7 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If S3 / Azure / GCS is not available in the target environment → fall back to a self-hosted MinIO; the contract (SSE, versioning, lifecycle) is the same.
- If envelope encryption breaks an existing backup → run the migration command (`migrate_backup_format`) before deploying; do not skip the header.
- If the drill command takes >10 minutes → reduce the artifact size for the drill; do not skip the round-trip.
