# INFRA-03: Test Strategy

> **Rule:** every test in this file must run against a real backend + MinIO. The **drill command is the gate** for the weekly CI job.

## 1. Unit Tests

### 1.1 Envelope encryption round-trip

```bash
cd backend
pytest apps/backups/tests/test_crypto.py -v
```

**Expected:** 1+ passed. The plaintext is recovered exactly.

### 1.2 Tampered ciphertext

```bash
pytest apps/backups/tests/test_crypto.py::test_tampered_ciphertext -v
```

**Expected:** `ValueError("checksum mismatch")` or `InvalidTag`.

### 1.3 Unknown KEK

```bash
pytest apps/backups/tests/test_crypto.py::test_unknown_kek -v
```

**Expected:** `KeyError("Unknown KEK: ...")`.

---

## 2. Integration Tests

### 2.1 S3 upload (MinIO)

```bash
cd backend
docker compose -f compose.yml -f infra/backup/compose.minio.yml up -d minio
pytest apps/backups/tests/test_upload_s3.py -v
docker compose -f compose.yml -f infra/backup/compose.minio.yml down
```

**Expected:** 3+ passed (upload, download, head).

### 2.2 Restore round-trip

```bash
pytest apps/backups/tests/test_restore_round_trip.py -v
```

**Expected:** 1+ passed. The restored bytes match the original.

### 2.3 Tampered object in S3

```bash
pytest apps/backups/tests/test_restore_round_trip.py::test_tampered_object_raises -v
```

**Expected:** `ValueError("checksum mismatch")`.

### 2.4 Retry on transient S3 error

```bash
pytest apps/backups/tests/test_upload_s3.py::test_retry_on_transient_error -v
```

**Expected:** 1+ passed (mocked `ClientError` triggers 3 retries).

---

## 3. End-to-End Tests

### 3.1 `drill_restore_from_external` against MinIO

```bash
docker compose -f compose.yml -f infra/backup/compose.minio.yml up -d
docker compose -f compose.yml exec backend python manage.py drill_restore_from_external --tenant=testco
echo "Exit code: $LASTEXITCODE"
# Expected: 0
docker compose -f compose.yml -f infra/backup/compose.minio.yml down
```

### 3.2 `drill` refuses a non-test tenant

```bash
docker compose -f compose.yml exec backend python manage.py drill_restore_from_external --tenant=acme
echo "Exit code: $LASTEXITCODE"
# Expected: 1 (refused)
```

### 3.3 S3 object has SSE-KMS metadata

```bash
aws s3api head-object --bucket mhami-backups --key testco/backup-2030-01-01.tar.age | jq .ServerSideEncryption
# Expected: "aws:kms"
```

### 3.4 Local backup still works

```bash
docker compose -f compose.yml exec backend python manage.py shell -c "
from apps.backups.services import run_backup
from apps.tenancy.models import Company
co = Company.objects.first()
print(run_backup(co))
"
# Expected: <BackupRun: ...>
```

### 3.5 Weekly CI job

The `backup-drill` job in `.github/workflows/ci.yml` runs on `cron: '0 4 * * 1'`. It is also triggerable via `workflow_dispatch`.

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| Envelope round-trip | 1 | passed |
| Tampered ciphertext | 1 | ValueError |
| Unknown KEK | 1 | KeyError |
| S3 upload (MinIO) | 3 | passed |
| Restore round-trip | 1 | passed |
| Tampered object | 1 | ValueError |
| Retry on transient error | 1 | passed |
| Drill | 1 | passed |
| Drill refuses non-test | 1 | refused |
| SSE-KMS metadata | 1 | aws:kms |
| Local backup | 1 | passed |

---

## 5. Run Tests

### 5.1 Local

```bash
# 1. Boot MinIO
docker compose -f compose.yml -f infra/backup/compose.minio.yml up -d minio

# 2. Unit + integration
cd backend
pytest apps/backups/tests/ -v

# 3. Drill
docker compose -f compose.yml exec backend python manage.py drill_restore_from_external --tenant=testco

# 4. Refuse non-test
docker compose -f compose.yml exec backend python manage.py drill_restore_from_external --tenant=acme
```

### 5.2 CI

The `backup-drill` job runs weekly. The unit + integration tests run on every PR in the existing `backend` job.

### 5.3 Failure simulation

To prove the retry helper works:

```python
# apps/backups/tests/test_upload_s3.py
def test_retry_on_transient_error(monkeypatch, s3_uploader):
    calls = []
    def fake_put(**kw):
        calls.append(kw)
        if len(calls) < 3:
            raise ClientError({"Error": {"Code": "Throttling"}}, "PutObject")
        return {}
    monkeypatch.setattr(s3_uploader._client, "put_object", fake_put)
    s3_uploader.upload("k", b"x", {})
    assert len(calls) == 3
```

To prove the drill refuses non-test tenants:

```bash
docker compose -f compose.yml exec backend python manage.py drill_restore_from_external --tenant=acme
echo "Exit code: $LASTEXITCODE"
# Expected: 1
```

---

## 6. Cross-links

- [H-05 — Backup Encryption](../../02_HIGH_PRIORITY/H-05_BACKUP_ENCRYPTION/00_DISCOVERY.md) — partner upgrade that hardens the local encryption.
- [H-06 — Backup Postgres Restore](../../02_HIGH_PRIORITY/H-06_BACKUP_POSTGRES_RESTORE/00_DISCOVERY.md) — partner upgrade that exercises the restore flow.
- [QA-01 — Test Layers](..) — reuses the `make_company` factory for the drill.
- [INFRA-01 — Hardened Compose](..) — `BACKUP_S3_*` secrets are fail-fast in `compose.prod.yml`.
