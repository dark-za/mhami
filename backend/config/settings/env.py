"""Centralised environment configuration via Pydantic Settings.

The :class:`PlatformSettings` dataclass declares every environment variable
the platform reads, with sensible defaults for local development and
type-aware validators for production-critical fields. The
:func:`get_settings` cache returns the same instance for the lifetime of
the process so reading a setting is cheap.

Two safety nets remain in :mod:`config.settings.base`:

1. ``DJANGO_SECRET_KEY`` and ``AUDIT_HMAC_SECRET`` are checked after the
   settings load to enforce non-default values in production.
2. ``METRICS_TOKEN`` and ``BACKUP_EXTERNAL_URI`` are checked similarly.

The trade-off is that production ``ImproperlyConfigured`` errors still
fire at import time, but the actual *parsing* and *validation* of all
environment variables happens once through Pydantic.
"""

from __future__ import annotations

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    """Strongly-typed view of every platform environment variable."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Django core
    django_settings_module: str = "config.settings.dev"
    django_secret_key: str = "change-me"
    django_debug: bool = False
    django_allowed_hosts: str = ""

    # Audit / signing
    audit_hmac_secret: str = ""

    # Database
    postgres_db: str = "platform"
    postgres_user: str = "platform"
    postgres_password: str = "platform"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Redis / cache / celery
    redis_url: str = "redis://redis:6379/0"
    cache_url: str = "redis://redis:6379/2"
    celery_result_backend: str = "redis://redis:6379/1"

    # Secrets
    mfa_encryption_keys: str = ""
    metrics_token: str = ""
    backup_external_uri: str = ""

    # Backup storage
    backup_storage_root: str = ""
    backup_restore_root: str = ""

    # Runtime
    gunicorn_workers: int = 3
    celery_log_level: str = "INFO"
    celery_worker_concurrency: int = 2
    frontend_port: int = 8080

    @field_validator("django_debug", mode="before")
    @classmethod
    def coerce_debug(cls, value: object) -> bool:
        """Parse the standard truthy strings used in deploy manifests."""
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        if isinstance(value, bool):
            return value
        return False


@lru_cache(maxsize=1)
def get_settings() -> PlatformSettings:
    """Return a cached :class:`PlatformSettings` instance.

    Pydantic-settings caches internally but ``lru_cache`` lets callers in
    different import paths share the same object identity.
    """
    return PlatformSettings()


def parse_env_list(value: str) -> list[str]:
    """Accept JSON arrays and comma-separated strings for list-shaped env vars."""
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        parsed = json.loads(stripped)
        if not isinstance(parsed, list):
            raise ValueError("Expected a JSON list.")
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in stripped.split(",") if item.strip()]


__all__ = ["PlatformSettings", "get_settings", "parse_env_list"]
