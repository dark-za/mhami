# H-05: Implement Fernet encryption for backups

## Discovery

### Problem
`apps/backups/services.py:196`:
```python
"encryption": {"encrypted": False, "algorithm": None}
```

### Impact
- Unencrypted copies on disk
- BACKUP_EXTERNAL_URI not used
- Violates RRK-001 (PHASE12)

### Fix

**File:** `apps/backups/services.py`

```python
from cryptography.fernet import Fernet
from django.conf import settings

def _get_backup_fernet() -> Fernet:
    """Resolve Fernet key from BACKUP_ENCRYPTION_KEY env var."""
    key = settings.BACKUP_ENCRYPTION_KEY
    if not key:
        raise ValueError("BACKUP_ENCRYPTION_KEY must be set")
    return Fernet(key.encode())


def _encrypt_artifact(data: bytes) -> tuple[bytes, str]:
    """Encrypt backup data with Fernet (AES-128-CBC + HMAC-SHA256)."""
    fernet = _get_backup_fernet()
    encrypted = fernet.encrypt(data)
    return encrypted, _sha256(encrypted)


def _decrypt_artifact(encrypted: bytes) -> bytes:
    fernet = _get_backup_fernet()
    return fernet.decrypt(encrypted)


def complete_backup_run(*args, **kwargs):
    # ... existing code ...

    # ✅ Encrypt before writing
    with zipfile.ZipFile(archive_path, "rb") as zf:
        plaintext = zf.read()

    encrypted_data, encrypted_sha = _encrypt_artifact(plaintext)
    encrypted_path = storage_root / f"{backup_run.id}.enc"
    encrypted_path.write_bytes(encrypted_data)

    backup_run.artifact_sha256 = encrypted_sha
    backup_run.manifest["encryption"] = {
        "encrypted": True,
        "algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)",
    }
    backup_run.save()
```

### Acceptance Standards
- AC-1: backup artifact encrypted on disk
- AC-2: SHA-256 of the encrypted data
- AC-3: restore decrypts successfully
- AC-4: BACKUP_ENCRYPTION_KEY mandatory in production
- AC-5: 3+ tests for encrypt/decrypt roundtrip

### Tests
```python
def test_backup_artifact_is_encrypted():
    run = create_backup_run(...)
    artifact = download_backup_artifact(...)
    plaintext = artifact.read_bytes()
    # Must NOT start with "PK" (zip magic)
    assert not plaintext.startswith(b"PK")

def test_backup_restore_decrypts_correctly():
    run = create_backup_run(...)
    decrypted = decrypt_backup_artifact(...)
    assert decrypted.startswith(b"PK")

def test_missing_encryption_key_fails():
    with override_settings(BACKUP_ENCRYPTION_KEY=""):
        with pytest.raises(ValueError):
            _get_backup_fernet()
```
