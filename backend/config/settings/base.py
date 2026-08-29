"""Django settings bootstrapped from :mod:`config.settings.env`.

The module reads every environment variable through :func:`get_settings`
to provide type-safe configuration. Production-critical secrets
(``DJANGO_SECRET_KEY``, ``AUDIT_HMAC_SECRET``, ``METRICS_TOKEN``,
``BACKUP_EXTERNAL_URI``, and backup encryption settings) are still validated here so that a missing or
default value fails fast at import time.
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

from .env import get_settings, parse_env_list

BASE_DIR = Path(__file__).resolve().parents[3]

settings = get_settings()

# ---------------------------------------------------------------------------
# Core secrets
# ---------------------------------------------------------------------------
if (
    settings.django_settings_module == "config.settings.prod"
    and (not settings.django_secret_key or settings.django_secret_key == "change-me")
):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set to a non-default value in production."
    )
SECRET_KEY = settings.django_secret_key

DEBUG = settings.django_debug
ALLOWED_HOSTS = parse_env_list(settings.django_allowed_hosts)

if (
    settings.django_settings_module == "config.settings.prod"
    and (not settings.audit_hmac_secret or settings.audit_hmac_secret == "change-me")
):
    raise ImproperlyConfigured(
        "AUDIT_HMAC_SECRET must be set to a non-default value in production."
    )
AUDIT_HMAC_SECRET = settings.audit_hmac_secret or SECRET_KEY

# MFA keys: fall back to a derived dev key if not provided.
if settings.mfa_encryption_keys:
    MFA_ENCRYPTION_KEYS = parse_env_list(settings.mfa_encryption_keys)
else:
    development_key = hashlib.sha256(f"{SECRET_KEY}:mhami:mfa".encode()).digest()
    MFA_ENCRYPTION_KEYS = [base64.urlsafe_b64encode(development_key).decode("ascii")]


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.platform_core.apps.PlatformCoreConfig",
    "apps.audit.apps.AuditConfig",
    "apps.identity.apps.IdentityConfig",
    "apps.tenancy.apps.TenancyConfig",
    "apps.organizations.apps.OrganizationsConfig",
    "apps.tasks.apps.TasksConfig",
    "apps.evidence.apps.EvidenceConfig",
    "apps.reviews.apps.ReviewsConfig",
    "apps.ai_gateway.apps.AiGatewayConfig",
    "apps.connector_control.apps.ConnectorControlConfig",
    "apps.agent_access.apps.AgentAccessConfig",
    "apps.exports.apps.ExportsConfig",
    "apps.backups.apps.BackupsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.pilot.apps.PilotConfig",
    "apps.compliance.apps.ComplianceConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.platform_core.request_id.RequestIDMiddleware",
    "apps.identity.middleware.MFAEnforcementMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": settings.postgres_db,
        "USER": settings.postgres_user,
        "PASSWORD": settings.postgres_password,
        "HOST": settings.postgres_host,
        "PORT": str(settings.postgres_port),
    }
}

AUTH_USER_MODEL = "identity.User"
AUTHENTICATION_BACKENDS = [
    "apps.tenancy.auth_backends.CompanyCodeBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Sessions / CSRF / Locale
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 12
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SAMESITE = "Lax"
# C-04: explicitly opt in to issuing the CSRF cookie on safe (GET)
# requests. Without this Django's `CsrfViewMiddleware` only sets the
# cookie when the response goes through a CSRF-protected flow, which
# leaves the browser without a token on the very first mutation. The
# bootstrap endpoint below is the documented entry point for clients
# to obtain the cookie.
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Files / media / backups
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
BACKUP_STORAGE_ROOT = Path(settings.backup_storage_root) if settings.backup_storage_root else (MEDIA_ROOT / "backups")
BACKUP_RESTORE_ROOT = Path(settings.backup_restore_root) if settings.backup_restore_root else (MEDIA_ROOT / "backup-restores")
DATABASES["backup_restore"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": str(BACKUP_RESTORE_ROOT / "restore.sqlite3"),
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.platform_core.errors.platform_exception_handler",
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": settings.cache_url,
    }
}

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "registration_ip": "5/hour",
    "login_ip": "60/minute",
    "login_account": "5/minute",
    "mfa_user": "10/minute",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Mhami API",
    "DESCRIPTION": "Foundation API contract for the modular operations platform.",
    "VERSION": "0.1.0",
}

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = settings.redis_url
CELERY_RESULT_BACKEND = settings.celery_result_backend
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_ROUTES = {
    "apps.backups.run_backup_run": {"queue": "media"},
    "apps.exports.run_export_request": {"queue": "media"},
}

CELERY_BEAT_SCHEDULE = {
    # C-11: explicit scheduling of every lifecycle job. The beat
    # scheduler is the single entry point so a deployment cannot run a
    # subset of the jobs by accident.
    "process-lifecycle-expirations-daily": {
        "task": "apps.tenancy.process_lifecycle_expirations",
        "schedule": crontab(hour=2, minute=0),
    },
    "create-daily-backups": {
        "task": "apps.backups.create_daily_backups",
        "schedule": crontab(hour=2, minute=30),
    },
    "cleanup-expired-exports-hourly": {
        "task": "apps.exports.cleanup_expired_exports",
        "schedule": crontab(minute=0),
    },
    "process-notification-outbox": {
        "task": "apps.notifications.process_outbox_events",
        "schedule": crontab(minute="*/5"),
    },
    "run-scheduler-quarter-hourly": {
        "task": "apps.tasks.run_scheduler",
        "schedule": crontab(minute="*/15"),
    },
    "mark-overdue-tasks-quarter-hourly": {
        "task": "apps.tasks.mark_overdue",
        "schedule": crontab(minute="*/15"),
    },
    "cleanup-expired-capture-sessions-every-5-min": {
        "task": "apps.evidence.cleanup_expired_sessions",
        "schedule": crontab(minute="*/5"),
    },
}

# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------
PLATFORM_CORE_VERSION = "0.1.0"
PLATFORM_MODULES = [
    "platform_core",
    "audit",
    "identity",
    "tenancy",
    "organizations",
    "tasks",
    "evidence",
    "reviews",
    "ai_gateway",
    "connector_control",
    "agent_access",
    "exports",
    "backups",
    "notifications",
    "pilot",
]


# ---------------------------------------------------------------------------
# Production-critical tokens
# ---------------------------------------------------------------------------
METRICS_TOKEN = settings.metrics_token
BACKUP_EXTERNAL_URI = settings.backup_external_uri
BACKUP_ENCRYPTION_KEY = settings.backup_encryption_key
BACKUP_EXTERNAL_KEY_ID = settings.backup_external_key_id
BACKUP_EXTERNAL_KEYS = settings.backup_external_keys
BACKUP_EXTERNAL_REGION = settings.backup_external_region
BACKUP_EXTERNAL_ENDPOINT = settings.backup_external_endpoint
BACKUP_EXTERNAL_SSE = settings.backup_external_sse
BACKUP_EXTERNAL_KMS_KEY_ID = settings.backup_external_kms_key_id
BACKUP_EXTERNAL_RETENTION_DAYS = settings.backup_external_retention_days
BACKUP_RESTORE_DB_ENGINE = settings.backup_restore_db_engine
BACKUP_RESTORE_DB_NAME = settings.backup_restore_db_name
BACKUP_RESTORE_DB_USER = settings.backup_restore_db_user
BACKUP_RESTORE_DB_PASSWORD = settings.backup_restore_db_password
BACKUP_RESTORE_DB_HOST = settings.backup_restore_db_host
BACKUP_RESTORE_DB_PORT = settings.backup_restore_db_port
AI_PROVIDER_API_KEY = settings.ai_provider_api_key
AI_PROVIDER_ALLOWED_ENDPOINTS = parse_env_list(settings.ai_provider_allowed_endpoints)
AI_PROVIDER_TIMEOUT_SECONDS = settings.ai_provider_timeout_seconds

if (
    settings.django_settings_module == "config.settings.prod"
    and (not METRICS_TOKEN or METRICS_TOKEN == "replace-with-a-long-random-monitoring-token")
):
    raise ImproperlyConfigured(
        "METRICS_TOKEN must be set to a non-default value in production."
    )
if (
    settings.django_settings_module == "config.settings.prod"
    and (not BACKUP_EXTERNAL_URI or "replace-with-approved" in BACKUP_EXTERNAL_URI)
):
    raise ImproperlyConfigured(
        "BACKUP_EXTERNAL_URI must be set to an approved destination in production."
    )
if settings.django_settings_module == "config.settings.prod" and not BACKUP_ENCRYPTION_KEY:
    raise ImproperlyConfigured(
        "BACKUP_ENCRYPTION_KEY must be set to an independent Fernet key in production."
    )
if settings.django_settings_module == "config.settings.prod" and BACKUP_EXTERNAL_URI:
    if not BACKUP_EXTERNAL_KEY_ID or not BACKUP_EXTERNAL_KEYS:
        raise ImproperlyConfigured(
            "BACKUP_EXTERNAL_KEY_ID and BACKUP_EXTERNAL_KEYS must be set when external backups are enabled."
        )
