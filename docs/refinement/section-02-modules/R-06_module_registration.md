# R-06: توحيد Module Registration عبر AppConfig

> **Status:** ✅ Completed (2026-08-28) — 14/14 modules migrated, registry discovers via AppConfig.

## الهدف
كل module عنده `apps.py` و `manifest.py` يدوياً. الهدف: توحيدهما في `PlatformAppConfig` بحيث يكون `manifest` مجرد class attribute على الـ AppConfig، وتتمّ قراءة الـ registry مباشرة من الـ `INSTALLED_APPS`.

## الوضع قبل
```python
# apps/tenancy/apps.py
class TenancyConfig(AppConfig):
    name = "apps.tenancy"
    default_auto_field = "django.db.models.BigAutoField"

# apps/tenancy/manifest.py
from apps.platform_core.registry import quick_manifest
module_manifest = quick_manifest(
    slug="tenancy",
    dependencies=("platform_core", "identity"),
    permissions=("tenancy.manage_company",),
    events_published=("tenancy.company.created", "tenancy.company.updated"),
)

# apps/platform_core/registry.py
@classmethod
def discover(cls) -> "ModuleRegistry":
    for slug in settings.PLATFORM_MODULES:
        module = import_module(f"apps.{slug}.manifest")
        ...
```

## التغيير النهائي

### 1. `PlatformAppConfig` base class
```python
# filepath: backend/apps/platform_core/apps.py
class PlatformAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    manifest: "ModuleManifest | None" = None

    def ready(self) -> None:
        super().ready()
        if self.manifest is None:
            return
        from .registry import ModuleRegistry
        ModuleRegistry.register_manifest(self.manifest)


class PlatformCoreConfig(PlatformAppConfig):
    name = "apps.platform_core"
    verbose_name = "Platform Core"
    manifest = quick_manifest(slug="platform_core", events_published=("core.health.changed",))
```

### 2. كل module apps.py
```python
# filepath: backend/apps/tenancy/apps.py
from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest

class TenancyConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenancy"
    manifest = quick_manifest(
        slug="tenancy",
        dependencies=("platform_core", "identity"),
        permissions=("tenancy.manage_company",),
        events_published=("tenancy.company.created", "tenancy.company.updated"),
    )
```

### 3. `INSTALLED_APPS` صريح
```python
# filepath: backend/config/settings/base.py
INSTALLED_APPS = [
    ...,
    "apps.platform_core.apps.PlatformCoreConfig",
    "apps.audit.apps.AuditConfig",
    "apps.identity.apps.IdentityConfig",
    "apps.tenancy.apps.TenancyConfig",
    ...,
]
```

### 4. `ModuleRegistry.discover()` يقرأ من AppConfigs أولاً
```python
# filepath: backend/apps/platform_core/registry.py
@classmethod
def discover(cls) -> "ModuleRegistry":
    manifests: list[ModuleManifest] = []
    seen: set[str] = set()
    from django.apps import apps as global_apps
    # Primary: AppConfig.manifest
    for cfg in global_apps.get_app_configs():
        manifest = getattr(cfg, "manifest", None)
        if isinstance(manifest, ModuleManifest):
            manifests.append(manifest)
            seen.add(manifest.slug)
    # Fallback: legacy manifest.py
    for slug in settings.PLATFORM_MODULES:
        if slug in seen:
            continue
        try:
            module = import_module(f"apps.{slug}.manifest")
        except ModuleNotFoundError:
            continue
        manifest = getattr(module, "module_manifest", None)
        if not isinstance(manifest, ModuleManifest):
            raise ModuleRegistryError(f"Module {slug} does not expose module_manifest")
        manifests.append(manifest)
        seen.add(slug)
    registry = cls(manifests)
    registry.validate()
    return registry

@classmethod
def register_manifest(cls, manifest: ModuleManifest) -> None:
    """Register on the cached singleton (called by AppConfig.ready)."""
    get_registry().register(manifest)
```

## الأثر الفعلي
- ✅ **+2 helper** في `platform_core/apps.py` (~40 سطر)
- ✅ **14 `apps/<module>/apps.py`** تحوّلت إلى `PlatformAppConfig` مع `manifest` attribute (~14 سطر/ملف)
- ⏸️ **14 `manifest.py` باقية** كـ re-export ضمني (سيُحذف في commit لاحق)
- ✅ **`PLATFORM_MODULES` في settings** يبقى كما هو (مصدر الحقيقة للـ `INSTALLED_APPS`)، fallback للوحدات غير المحوّلة
- 🟢 **Single source of truth:** اسم الـ module من `AppConfig`

## التحقق
```bash
$env:DJANGO_SETTINGS_MODULE="config.settings.test"
python -c "import django; django.setup(); from apps.platform_core.registry import get_registry; r = get_registry(); print(len(r.manifests))"
# -> 14
pytest apps/platform_core/tests/test_registry.py -v   # 3/3 ✅
pytest apps/ -q                                        # 79 passed, 5 pre-existing failures
ruff check apps/                                       # All checks passed!
mypy apps/platform_core/apps.py apps/platform_core/registry.py  # Success: no issues
python manage.py check                                 # System check identified no issues
```

## معايير القبول
- [x] كل الـ 14 modules تستخدم `PlatformAppConfig`
- [x] `INSTALLED_APPS` يذكر الـ config classes صراحة
- [x] `registry.discover()` يجد 14 module بنفس الـ metadata
- [x] `manifest.py` يبقى قابلاً للحذف (لا أحد يستورده)
- [x] `pytest apps/platform_core/tests/test_registry.py -v` -> 3 passed

## المخاطر
🟢 **منخفضة** — `ModuleRegistry.register_manifest` يستخدم singleton cached في `get_registry()`، فالترتيب بين `AppConfig.ready()` و `discover()` لا يهم.

## احتياطات
- ✅ `manifest.py` لم يُحذف (يبقى كـ re-export fallback كما هو مخطط)
- ✅ `PLATFORM_MODULES` ما زال يُقرأ في `discover()` (fallback) — يضمن توافق الأنواع القديمة
