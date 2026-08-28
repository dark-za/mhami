from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


ENCRYPTED_VALUE_PREFIX = "fernet:v1:"


@lru_cache(maxsize=1)
def _cipher() -> MultiFernet:
    try:
        keys = [Fernet(key.encode("ascii")) for key in settings.MFA_ENCRYPTION_KEYS]
    except (AttributeError, TypeError, ValueError) as exc:
        raise ImproperlyConfigured("MFA_ENCRYPTION_KEYS contains an invalid Fernet key.") from exc
    if not keys:
        raise ImproperlyConfigured("MFA_ENCRYPTION_KEYS must contain at least one Fernet key.")
    return MultiFernet(keys)


def encrypt_secret(value: str) -> str:
    if not value or value.startswith(ENCRYPTED_VALUE_PREFIX):
        return value
    token = _cipher().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{ENCRYPTED_VALUE_PREFIX}{token}"


def decrypt_secret(value: str) -> str:
    if not value or not value.startswith(ENCRYPTED_VALUE_PREFIX):
        return value
    token = value.removeprefix(ENCRYPTED_VALUE_PREFIX)
    try:
        return _cipher().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise ImproperlyConfigured(
            "An MFA secret cannot be decrypted with the configured encryption keys."
        ) from exc


class EncryptedSecretField(models.CharField):
    description = "Application-encrypted secret"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_secret(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        return encrypt_secret(value)
