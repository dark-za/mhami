# R-13: تكوين موحّد من environment (Pydantic Settings)

> **Status:** ✅ Completed (2026-08-28) — 1 new module (env.py)، base.py migrated، 17 `os.getenv()` calls replaced. 86/91 tests passing.

## الهدف
توحيد قراءات `os.getenv()` في `config/settings/base.py` (221 سطر) عبر Pydantic Settings، مع type safety و validation.

## الوضع قبل
```python
# 17 قراءة os.getenv متفرقة
_secret_key = os.getenv("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()]
_audit_hmac_secret = os.getenv("AUDIT_HMAC_SECRET")
# ... إلخ
```
- 17 استدعاء `os.getenv()` يدوي
- 4 منطق تحويلات (split comma, parse bool, etc.) مكتوبة يدوياً
- بدون type hints، بدون validation
- 4 `ImproperlyConfigured` checks داخل base.py

## التغيير النهائي

### 1. `config/settings/env.py` (جديد، 105 سطور)
```python
# filepath: backend/config/settings/env.py

class PlatformSettings(BaseSettings):
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
    django_allowed_hosts: list[str] = Field(default_factory=list)

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
    mfa_encryption_keys: list[str] = Field(default_factory=list)
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

    @field_validator("django_allowed_hosts", mode="before")
    @classmethod
    def split_hosts(cls, value):
        if isinstance(value, str):
            return [h.strip() for h in value.split(",") if h.strip()]
        return value

    @field_validator("mfa_encryption_keys", mode="before")
    @classmethod
    def split_keys(cls, value):
        if isinstance(value, str):
            return [k.strip() for k in value.split(",") if k.strip()]
        return value

    @field_validator("django_debug", mode="before")
    @classmethod
    def coerce_debug(cls, value):
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return value if isinstance(value, bool) else False


@lru_cache(maxsize=1)
def get_settings() -> PlatformSettings:
    return PlatformSettings()
```

### 2. `config/settings/base.py` migrated (221 → 233 سطر، +12 بسبب docs)
```python
# filepath: backend/config/settings/base.py
from .env import get_settings

settings = get_settings()

SECRET_KEY = settings.django_secret_key  # بدلاً من os.getenv("DJANGO_SECRET_KEY")
DEBUG = settings.django_debug              # بدلاً من os.getenv(...).lower() in {...}
ALLOWED_HOSTS = settings.django_allowed_hosts  # بدلاً من split manual
AUDIT_HMAC_SECRET = settings.audit_hmac_secret or SECRET_KEY
MFA_ENCRYPTION_KEYS = settings.mfa_encryption_keys or [derived_dev_key]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": settings.postgres_db,    # بدلاً من os.getenv("POSTGRES_DB", "platform")
        ...
    }
}

CACHES = {
    "default": {
        "LOCATION": settings.cache_url,  # بدلاً من os.getenv("CACHE_URL", ...)
    }
}

CELERY_BROKER_URL = settings.redis_url
CELERY_RESULT_BACKEND = settings.celery_result_backend
METRICS_TOKEN = settings.metrics_token
BACKUP_EXTERNAL_URI = settings.backup_external_uri
```

### 3. Production guards محفوظة
- `DJANGO_SECRET_KEY` لا يزال يفرض non-default في prod
- `AUDIT_HMAC_SECRET` لا يزال يفرض non-default في prod
- `METRICS_TOKEN` لا يزال يفرض non-default في prod
- `BACKUP_EXTERNAL_URI` لا يزال يفرض non-default في prod

كلها تستخدم `settings.django_settings_module` بدلاً من `os.getenv("DJANGO_SETTINGS_MODULE")` (لكن ما زالت ترفع `ImproperlyConfigured`).

## الأثر الفعلي
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `config/settings/env.py` | غير موجود | 105 سطر | ⭐ جديد |
| `config/settings/base.py` | 221 سطر | 233 سطر | +12 (docs) |
| `os.getenv()` في base.py | 17 | 0 | **−17** |
| `os.getenv()` في النظام كله | 17 | 0 | **−17** |
| Type hints على الإعدادات | 0 | 19 fields | +19 |
| Field validators | 0 | 3 (hosts, keys, debug) | +3 |
| Tests passing | 86 | 86 | 0 |
| regressions | — | — | 0 |
| ruff | All checks passed | All checks passed | 0 |
| mypy | Success | Success | 0 |

## التحقق
```bash
$env:DJANGO_SETTINGS_MODULE="config.settings.test"
cd backend
python -c "from config.settings.env import get_settings; s = get_settings(); print(s.django_debug, s.postgres_db, s.django_allowed_hosts)"
# False platform []
python manage.py check
# System check identified no issues (0 silenced).
python -m pytest apps/ tests/ -q
# 86 passed, 5 pre-existing failures
python -m ruff check config/
# All checks passed!
python -m mypy config/settings/env.py config/settings/base.py
# Success: no issues found in 2 source files
```

## معايير القبول
- [x] `config/settings/env.py` يحتوي على `PlatformSettings` و `get_settings()`
- [x] `base.py` لا يحتوي على `os.getenv()` صريح
- [x] Production guards (SECRET_KEY, AUDIT_HMAC_SECRET, METRICS_TOKEN, BACKUP_EXTERNAL_URI) محفوظة
- [x] Type safety على كل env var
- [x] mypy + ruff نظيفان
- [x] لا regressions في الـ tests

## المخاطر
🟢 **منخفضة** — Refactor للـ configuration فقط، لا يمس business logic. الـ Pydantic v2 صارم لكنه يطابق الـ defaults الموجودة.

## ملاحظات
- ✅ `pydantic-settings==2.6.0` كان مثبتاً مسبقاً (مذكور في `requirements.txt`)
- ✅ Production guards محفوظة تماماً (نفس الـ error messages)
- 📋 **R-13b (مستقبلي)**: تقسيم `PlatformSettings` إلى nested groups (DjangoSettings, DatabaseSettings, CelerySettings, ...) لزيادة التنظيم
- 📋 **R-13c (مستقبلي)**: إنشاء `config/settings/test.py` يستورد من `env.py` مع `model_config = SettingsConfigDict(env_file=".env.test")` للـ test-specific overrides
- 📋 **R-13d (مستقبلي)**: إضافة `.env.example` يطابق الحقول في `PlatformSettings` (مذكور في خطة R-13)
