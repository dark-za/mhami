"""H-05 regression tests: backup encryption with Fernet.

The artefact on disk must be the Fernet-wrapped payload, not the raw
zip. Round-tripping the bytes through ``_encrypt_artifact`` and
``_decrypt_artifact`` must return the original zip.
"""

from __future__ import annotations


import pytest
from cryptography.fernet import Fernet

from apps.backups.services import (
    _decrypt_artifact,
    _encrypt_artifact,
    _get_backup_fernet,
)

pytestmark = pytest.mark.django_db


def test_fernet_uses_configured_key(settings):
    key = Fernet.generate_key().decode("ascii")
    settings.BACKUP_ENCRYPTION_KEY = key
    fernet = _get_backup_fernet()
    assert isinstance(fernet, Fernet)


def test_encrypt_decrypt_roundtrip(settings):
    settings.BACKUP_ENCRYPTION_KEY = Fernet.generate_key().decode("ascii")
    payload = b"hello mhami backup" * 32
    encrypted, digest = _encrypt_artifact(payload)
    assert encrypted != payload
    assert len(digest) == 64
    decrypted = _decrypt_artifact(encrypted)
    assert decrypted == payload


def test_fernet_rejects_tampered_ciphertext(settings):
    settings.BACKUP_ENCRYPTION_KEY = Fernet.generate_key().decode("ascii")
    payload = b"important tenant data"
    encrypted, _ = _encrypt_artifact(payload)
    tampered = encrypted[:-4] + b"AAAA"
    with pytest.raises(Exception):
        _decrypt_artifact(tampered)
