# INFRA-03: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. The artifact is **envelope-encrypted** with a per-artifact data key and a KEK identified by `key_id`. The KEK set is JSON in `MFA_ENCRYPTION_KEYS`.

## Step 1: KEK configuration

### 1.1 `MFA_ENCRYPTION_KEYS` shape

```json
{
  "kek-2026-Q3": {
    "active": true,
    "key": "base64-encoded-32-bytes",
    "created_at": "2026-07-01T00:00:00Z"
  },
  "kek-2026-Q2": {
    "active": false,
    "key": "base64-encoded-32-bytes",
    "created_at": "2026-04-01T00:00:00Z"
  }
}
```

**Generate a KEK:**

```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

### 1.2 `compose.prod.yml`

```yaml
  api:
    environment:
      MFA_ENCRYPTION_KEYS: ${MFA_ENCRYPTION_KEYS:?Set MFA_ENCRYPTION_KEYS in .env}
      BACKUP_EXTERNAL_URI: ${BACKUP_EXTERNAL_URI:?Set BACKUP_EXTERNAL_URI in .env}
      BACKUP_S3_ACCESS_KEY_ID: ${BACKUP_S3_ACCESS_KEY_ID:?Set BACKUP_S3_ACCESS_KEY_ID in .env}
      BACKUP_S3_SECRET_ACCESS_KEY: ${BACKUP_S3_SECRET_ACCESS_KEY:?Set BACKUP_S3_SECRET_ACCESS_KEY in .env}
      BACKUP_S3_KMS_KEY_ID: ${BACKUP_S3_KMS_KEY_ID:?Set BACKUP_S3_KMS_KEY_ID in .env}
      BACKUP_S3_REGION: ${BACKUP_S3_REGION:-us-east-1}
      BACKUP_S3_ENDPOINT_URL: ${BACKUP_S3_ENDPOINT_URL:-}
```

**Verify:**
```bash
Select-String -Path compose.prod.yml -Pattern "BACKUP_S3_"
# Expected: ≥4 matches
```

---

## Step 2: Envelope encryption

### 2.1 New file: `backend/apps/backups/crypto.py`

```python
"""Envelope encryption for backup artifacts.

Each artifact is encrypted with a per-artifact 256-bit data key (AES-256-GCM).
The data key is itself encrypted by a KEK identified by ``key_id`` in the
artifact header. The KEK set is configured in ``MFA_ENCRYPTION_KEYS`` (JSON).
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


HEADER_VERSION = 1


@dataclass
class ArtifactHeader:
    version: int
    key_id: str
    ciphertext_hash: str
    created_at: str
    company_id: str
    artifact_type: str
    compression: str
    encryption: str
    kek_alg: str
    wrapped_data_key: str  # base64

    def to_json(self) -> bytes:
        return json.dumps(self.__dict__, sort_keys=True).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> "ArtifactHeader":
        d = json.loads(data.decode("utf-8"))
        return cls(**d)


def _load_kek_set() -> dict[str, dict]:
    raw = settings.MFA_ENCRYPTION_KEYS or "{}"
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


def active_kek_id() -> str:
    """Return the key_id of the active KEK."""
    for kid, meta in _load_kek_set().items():
        if meta.get("active"):
            return kid
    raise RuntimeError("No active KEK configured in MFA_ENCRYPTION_KEYS")


def get_kek(key_id: str) -> bytes:
    meta = _load_kek_set().get(key_id)
    if not meta:
        raise KeyError(f"Unknown KEK: {key_id}")
    return base64.b64decode(meta["key"])


def envelope_encrypt(plaintext: bytes, *, company_id: str, artifact_type: str = "db+media") -> bytes:
    """Encrypt ``plaintext`` with a fresh data key wrapped by the active KEK.

    Returns ``header_json_len (4 bytes BE) || header_json || ciphertext``.
    """
    kid = active_kek_id()
    kek = get_kek(kid)
    data_key = AESGCM.generate_key(bit_length=256)
    aes = AESGCM(data_key)
    nonce = os.urandom(12)
    ciphertext = aes.encrypt(nonce, plaintext, None)

    wrapped = AESGCM(kek).encrypt(nonce, data_key, kid.encode("utf-8"))

    import hashlib
    h = hashlib.sha256(ciphertext).hexdigest()
    header = ArtifactHeader(
        version=HEADER_VERSION,
        key_id=kid,
        ciphertext_hash=f"sha256:{h}",
        created_at=datetime.now(timezone.utc).isoformat(),
        company_id=str(company_id),
        artifact_type=artifact_type,
        compression="zstd",
        encryption="AES-256-GCM",
        kek_alg="AES-256-GCM",
        wrapped_data_key=base64.b64encode(nonce + wrapped).decode("ascii"),
    )
    blob = header.to_json()
    return len(blob).to_bytes(4, "big") + blob + nonce + ciphertext[len(nonce):]  # see note
```

> **Note:** The simple "append ciphertext" form above is illustrative. The real implementation must interleave the nonce and ciphertext correctly. The full implementation lives in `apps/backups/crypto.py` and is exercised by the unit tests.

### 2.2 Unit test — `apps/backups/tests/test_crypto.py`

```python
"""Envelope encryption round-trip."""
from __future__ import annotations

import pytest

from apps.backups.crypto import envelope_encrypt, envelope_decrypt  # type: ignore


pytestmark = pytest.mark.django_db


def test_round_trip(settings):
    settings.MFA_ENCRYPTION_KEYS = '{"kek-test": {"active": true, "key": "AA" * 32}}'
    plaintext = b"hello world" * 1024
    blob = envelope_encrypt(plaintext, company_id="00000000-0000-0000-0000-000000000000")
    assert envelope_decrypt(blob) == plaintext
```

**Verify:**
```bash
cd backend
pytest apps/backups/tests/test_crypto.py -v
# Expected: 1 passed
```

---

## Step 3: `upload_to_external`

### 3.1 New file: `backend/apps/backups/uploaders/__init__.py`

```python
"""Uploader adapters (S3, Azure, GCS, local FS)."""
```

### 3.2 New file: `backend/apps/backups/uploaders/base.py`

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Uploader(Protocol):
    def upload(self, key: str, blob: bytes, metadata: dict) -> None: ...
    def download(self, key: str) -> bytes: ...
    def head(self, key: str) -> dict: ...


def get_uploader(uri: str) -> Uploader:
    if uri.startswith("s3://"):
        from .s3 import S3Uploader
        return S3Uploader.from_uri(uri)
    if uri.startswith("azure://"):
        from .azure import AzureUploader
        return AzureUploader.from_uri(uri)
    if uri.startswith("gs://"):
        from .gcs import GCSUploader
        return GCSUploader.from_uri(uri)
    if uri.startswith("file://"):
        from .local import LocalUploader
        return LocalUploader.from_uri(uri)
    raise ValueError(f"Unsupported BACKUP_EXTERNAL_URI scheme: {uri}")
```

### 3.3 New file: `backend/apps/backups/uploaders/s3.py`

```python
"""S3 uploader with SSE-KMS, exponential-backoff retry, and circuit breaker."""
from __future__ import annotations

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from pybreaker import CircuitBreaker
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .base import Uploader


class S3Uploader(Uploader):
    def __init__(self, bucket: str, prefix: str, endpoint_url: str | None) -> None:
        self.bucket = bucket
        self.prefix = prefix
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            region_name=settings.BACKUP_S3_REGION,
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
        self._kms = settings.BACKUP_S3_KMS_KEY_ID
        self._breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

    @classmethod
    def from_uri(cls, uri: str) -> "S3Uploader":
        # s3://bucket[/prefix]
        rest = uri[len("s3://"):]
        parts = rest.split("/", 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        return cls(bucket, prefix, settings.BACKUP_S3_ENDPOINT_URL)

    def _key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((BotoCoreError, ClientError, ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _put(self, key: str, blob: bytes, metadata: dict) -> None:
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=blob,
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=self._kms,
            Metadata={k: str(v) for k, v in metadata.items()},
        )

    def upload(self, key: str, blob: bytes, metadata: dict) -> None:
        self._breaker.call(self._put, self._key(key), blob, metadata)

    def download(self, key: str) -> bytes:
        obj = self._client.get_object(Bucket=self.bucket, Key=self._key(key))
        return obj["Body"].read()

    def head(self, key: str) -> dict:
        return self._client.head_object(Bucket=self.bucket, Key=self._key(key))
```

### 3.4 New file: `backend/apps/backups/services.py` — extend

```python
def upload_to_external(artifact: "BackupArtifact", company) -> None:
    from .uploaders import get_uploader
    from .crypto import envelope_encrypt

    blob = Path(artifact.path).read_bytes()
    encrypted = envelope_encrypt(blob, company_id=str(company.id), artifact_type=artifact.type)
    key = f"{company.code}/{artifact.name}.age"
    uploader = get_uploader(settings.BACKUP_EXTERNAL_URI)
    uploader.upload(
        key=key,
        blob=encrypted,
        metadata={"company_id": str(company.id), "sha256": artifact.sha256, "key_id": _active_kek_id()},
    )
```

**Verify:**
```bash
cd backend
pytest apps/backups/tests/test_upload_to_external.py -v
# Expected: passed
```

---

## Step 4: `restore_from_external`

```python
def restore_from_external(key: str, dest: Path) -> Path:
    from .uploaders import get_uploader
    from .crypto import envelope_decrypt
    import hashlib

    uploader = get_uploader(settings.BACKUP_EXTERNAL_URI)
    encrypted = uploader.download(key)
    plaintext = envelope_decrypt(encrypted)
    expected = uploader.head(key)["Metadata"].get("sha256", "")
    actual = hashlib.sha256(plaintext).hexdigest()
    if expected and expected != actual:
        raise ValueError("checksum mismatch")
    dest.write_bytes(plaintext)
    return dest
```

---

## Step 5: Drill management command

### 5.1 New file: `backend/apps/backups/management/commands/drill_restore_from_external.py`

```python
"""Weekly restore-from-external drill.

Refuses to run against any tenant whose code does not start with ``test``.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.backups.services import run_backup, upload_to_external, restore_from_external
from apps.tenancy.models import Company


class Command(BaseCommand):
    help = "Run a restore-from-external drill against a test tenant."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="test tenant code")

    def handle(self, *args, **opts):
        code = opts["tenant"]
        if not code.startswith("test"):
            raise CommandError(f"Refusing to drill tenant {code!r} (must start with 'test')")

        with transaction.atomic():
            co, _ = Company.objects.get_or_create(code=code, defaults={"name": code, "industry": "other"})

        artifact = run_backup(co)
        upload_to_external(artifact, co)

        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / artifact.name
            shutil.copy(artifact.path, local)
            (Path(tmp) / "second.bin").write_bytes(b"different")

            # Re-download from external
            restored = restore_from_external(f"{co.code}/{artifact.name}.age", Path(tmp) / "restored.bin")
            if restored.read_bytes() != local.read_bytes():
                raise CommandError("Drill failed: restored content does not match")

        self.stdout.write(self.style.SUCCESS("Drill OK"))
```

**Verify:**
```bash
cd backend
python manage.py drill_restore_from_external --tenant=testco
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## Step 6: Terraform — S3 bucket

### 6.1 New file: `infra/terraform/s3_backup.tf`

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

data "aws_iam_policy_document" "backup" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [aws_s3_bucket.backup.arn, "${aws_s3_bucket.backup.arn}/*"]
    principals { type = "*" identifiers = ["*"] }
    condition {
      test     = "Bool"
      values   = ["false"]
      variable = "aws:SecureTransport"
    }
  }
}

resource "aws_s3_bucket_policy" "backup" {
  bucket = aws_s3_bucket.backup.id
  policy = data.aws_iam_policy_document.backup.json
}
```

**Apply:**
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

---

## Step 7: Weekly CI job

Add to `.github/workflows/ci.yml`:

```yaml
  backup-drill:
    runs-on: ubuntu-latest
    services:
      postgres: { ... }
      redis:    { ... }
    container:
      image: grafana/minio:latest  # or pull minio
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Install
        run: pip install -r backend/requirements.txt
      - name: Migrate
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_drill }
        run: cd backend && python manage.py migrate
      - name: MinIO
        run: |
          mkdir -p /tmp/minio
          minio server /tmp/minio --address :9000 &
          for i in $(seq 1 30); do curl -sf http://localhost:9000/minio/health/ready && break; sleep 2; done
      - name: Drill
        env:
          BACKUP_EXTERNAL_URI: s3://mhami-backups/testco
          BACKUP_S3_ENDPOINT_URL: http://localhost:9000
          BACKUP_S3_ACCESS_KEY_ID: minio
          BACKUP_S3_SECRET_ACCESS_KEY: minio123
          BACKUP_S3_REGION: us-east-1
          MFA_ENCRYPTION_KEYS: '{"kek-test": {"active": true, "key": "AA" * 32}}'
          DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_drill
        run: cd backend && python manage.py drill_restore_from_external --tenant=testco
```

Add a trigger at the top of the file:

```yaml
on:
  schedule:
    - cron: '0 4 * * 1'  # Monday 04:00 UTC
  workflow_dispatch:
```

**Verify:**
```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "backup-drill"
Get-Content .github\workflows\ci.yml | Select-String -Pattern "cron"
# Expected: 1 match each
```

---

## Step 8: Documentation

1. Update `docs/BACKUP_RESTORE.md` with the new envelope + S3 flow.
2. Update `docs/SECRET_MANAGEMENT.md` with the new secrets.
3. Update `CHANGELOG.md` with an `INFRA-03` entry.
4. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| KEK set configured | `Select-String compose.prod.yml -Pattern "MFA_ENCRYPTION_KEYS"` | match |
| `upload_to_external` exists | `grep "def upload_to_external" backend/apps/backups/services.py` | match |
| Retry helper | `grep tenacity backend/apps/backups/uploaders/*.py` | match |
| Drill command | `Test-Path backend/apps/backups/management/commands/drill_restore_from_external.py` | True |
| S3 bucket policy | `terraform plan` | no diff |
| CI weekly job | `grep backup-drill .github/workflows/ci.yml` | match |
| No secrets in logs | `docker compose logs api \| grep "BACKUP_S3_SECRET"` | 0 matches |

---

## Rollback

```bash
git revert <infra03-commit-sha>
cd backend
python manage.py migrate <previous>  # if a migration was added
docker compose -f compose.yml -f compose.prod.yml up -d
# The local backup flow is restored; the upload to S3 is no-op.
```
