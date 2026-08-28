# R-02: توحيد ModuleManifest boilerplate

## الهدف
14 ملف `manifest.py` كلها بنفس البنية، فقط تختلف في slug, name, version, dependencies, permissions, events.

## الوضع الحالي
كل ملف ~15 سطر بنفس النمط:
```python
from apps.platform_core.registry import ModuleManifest
module_manifest = ModuleManifest(
    slug="tenancy", name="Tenancy", version="0.1.0",
    requires_core=">=0.1,<1.0",
    dependencies=("platform_core", "identity"),
    permissions=("tenancy.manage_company",),
    events_published=(...),
    events_consumed=(),
    healthcheck="tenancy.health",
    config_schema_version="1",
)
```

## التغيير

### 1. إضافة factory في `platform_core/registry.py`
```python
# filepath: backend/apps/platform_core/registry.py
def quick_manifest(
    slug: str,
    name: str | None = None,
    version: str = "0.1.0",
    dependencies: tuple[str, ...] = (),
    permissions: tuple[str, ...] = (),
    events_published: tuple[str, ...] = (),
    events_consumed: tuple[str, ...] = (),
    healthcheck: str | None = None,
) -> ModuleManifest:
    return ModuleManifest(
        slug=slug,
        name=name or slug.replace("_", " ").title(),
        version=version,
        requires_core=">=0.1,<1.0",
        dependencies=dependencies,
        permissions=permissions,
        events_published=events_published,
        events_consumed=events_consumed,
        healthcheck=healthcheck or f"{slug}.health",
        config_schema_version="1",
    )
```

### 2. تبسيط ملفات `manifest.py`
```python
# filepath: backend/apps/tenancy/manifest.py
from apps.platform_core.registry import quick_manifest
module_manifest = quick_manifest(
    slug="tenancy",
    dependencies=("platform_core", "identity"),
    permissions=("tenancy.manage_company",),
    events_published=("tenancy.company.created", "tenancy.company.updated"),
)
```

## الأثر
- ⬇️ **−200 سطر** في 14 ملف `manifest.py`
- ✅ نفس المخرجات في `module_manifest`
- ✅ لا تغيير في `registry.discover()`

## التحقق
```bash
python manage.py check
pytest apps/platform_core/tests/test_registry.py -v
```

## معايير القبول
- [ ] كل ملف `manifest.py` ≤ 8 أسطر
- [ ] `_core_version_supported` ينجح لكل الـ 14 module
- [ ] `registry.discover()` يرجع 14 manifest كما هو

## المخاطر
🟢 **منخفضة** — تكرار ميكانيكي
