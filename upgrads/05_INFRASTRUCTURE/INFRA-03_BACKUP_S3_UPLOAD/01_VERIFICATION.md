# INFRA-03: Verification Commands

> **Instructions:** Run baseline (Phase 1) before the change, then post-fix (Phase 2) to confirm the upload, the envelope encryption, and the restore drill.

## Phase 1: Pre-Fix Proof

### Command 1.1 — `BACKUP_EXTERNAL_URI` declared but not used

```bash
Select-String -Path compose.prod.yml -Pattern "BACKUP_EXTERNAL_URI"
# Expected: 1 match (env var)

Select-String -Path backend\apps\backups -Pattern "boto3|azure-storage-blob|google-cloud-storage" -Recurse
# Expected: 0 matches
```

### Command 1.2 — No envelope encryption

```bash
Select-String -Path backend\apps\backups -Pattern "envelope|key_id" -Recurse
# Expected: 0 matches
```

### Command 1.3 — No upload retry

```bash
Select-String -Path backend\apps\backups -Pattern "tenacity|backoff" -Recurse
# Expected: 0 matches
```

### Command 1.4 — No restore drill

```bash
Test-Path backend\apps\backups\management\commands\drill_restore_from_external.py
# Expected: False
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — `upload_to_external` exists

```bash
Select-String -Path backend\apps\backups\services.py -Pattern "def upload_to_external"
# Expected: 1 match
```

### Command 2.2 — Envelope encryption

```bash
Select-String -Path backend\apps\backups -Pattern "envelope|key_id" -Recurse
# Expected: ≥2 matches
```

### Command 2.3 — Retry helper

```bash
Select-String -Path backend\apps\backups -Pattern "tenacity|@retry" -Recurse
# Expected: ≥1 match
```

### Command 2.4 — Local round-trip with MinIO

```bash
docker compose -f compose.yml -f infra/backup/compose.minio.yml up -d minio
docker compose -f compose.yml exec backend python manage.py shell -c "
from apps.backups.services import run_backup, upload_to_external, restore_from_external
from apps.tenancy.models import Company
co = Company.objects.first()
artifact = run_backup(co)
upload_to_external(artifact, co)
restored = restore_from_external(artifact.key)
assert open(restored.path, 'rb').read() == open(artifact.path, 'rb').read(), 'round-trip mismatch'
print('OK')
"
# Expected: OK
```

### Command 2.5 — `drill_restore_from_external` command

```bash
docker compose -f compose.yml exec backend python manage.py drill_restore_from_external --tenant=testco
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### Command 2.6 — Header contains `key_id`, `ciphertext_hash`

```bash
docker compose -f compose.yml exec backend python manage.py shell -c "
from apps.backups.services import run_backup
from apps.tenancy.models import Company
co = Company.objects.first()
artifact = run_backup(co)
print(artifact.header)
"
# Expected: includes key_id, ciphertext_hash, version, created_at, company_id
```

### Command 2.7 — S3 object has SSE-KMS metadata

```bash
aws s3api head-object --bucket mhami-backups --key testco/backup-2030-01-01.tar.age | jq .ServerSideEncryption, .Metadata
# Expected: "aws:kms" and { "key_id": "...", "company_id": "...", "sha256": "..." }
```

### Command 2.8 — Restore fails on tampered artifact

```bash
docker compose -f compose.yml exec backend python manage.py shell -c "
from apps.backups.services import upload_to_external, restore_from_external
from apps.tenancy.models import Company
co = Company.objects.first()
# Tamper with the object in MinIO
import boto3
s3 = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minio', aws_secret_access_key='minio123')
s3.put_object(Bucket='mhami-backups', Key='testco/backup-2030-01-01.tar.age', Body=b'corrupted')
try:
    restore_from_external('testco/backup-2030-01-01.tar.age')
    print('UNEXPECTED: no error')
except ValueError as e:
    print('OK:', e)
"
# Expected: "OK: checksum mismatch"
```

### Command 2.9 — Weekly CI job

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "backup-drill"
# Expected: 1+ match

Get-Content .github\workflows\ci.yml | Select-String -Pattern "cron"
# Expected: 1+ match
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Local backup still works

```bash
docker compose -f compose.yml exec backend python manage.py shell -c "
from apps.backups.services import run_backup
from apps.tenancy.models import Company
co = Company.objects.first()
print(run_backup(co))
"
# Expected: <BackupRun: ...>
```

### Command 3.2 — Existing backup tests still pass

```bash
cd backend
pytest apps/backups/tests/ -v
# Expected: green
```

### Command 3.3 — Secrets are not logged

```bash
docker compose -f compose.yml logs api | Select-String -Pattern "BACKUP_S3_SECRET|MFA_ENCRYPTION_KEYS|AUDIT_HMAC_SECRET"
# Expected: 0 matches
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 / 1.4 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 / 2.6 / 2.7 / 2.8 / 2.9 green
- ✅ Command 3.1 / 3.2 / 3.3 no regression
