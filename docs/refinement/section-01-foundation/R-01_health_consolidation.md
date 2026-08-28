# R-01: توحيد health endpoints

## الهدف
كل module عنده ملف `health.py` بنفس المنطق (يرجع JSON). كلهم بنفس التوقيع تقريباً.

## الوضع الحالي
13 ملف `health.py` فيها:
```python
# platform_core
def live_status() / ready_status()
# باقي الـ 13:
def health() -> {"status": "ok", "module": "..."}  # متطابقة حرفياً
```

## التغيير

### 1. إنشاء `apps/platform_core/health_base.py`
```python
# filepath: backend/apps/platform_core/health_base.py
from __future__ import annotations
from django.http import JsonResponse
from django.http import HttpRequest

def make_health(module_slug: str):
    """Factory: تُرجع view موحّد لكل الـ modules"""
    def view(_request: HttpRequest | None = None):
        return JsonResponse({"status": "ok", "module": module_slug})
    view.__name__ = f"health_{module_slug}"
    return view

def liveness() -> dict[str, str]:
    return {"status": "ok"}

def readiness() -> dict[str, str]:
    # منطق فحص DB/Redis كما هو الآن
    ...
```

### 2. تبسيط كل ملف `health.py` في الـ modules
```python
# filepath: backend/apps/tenancy/health.py
from apps.platform_core.health_base import make_health
health = make_health("tenancy")
```

## الأثر
- ⬇️ **−150 سطر** في `apps/`
- ✅ لا تغيير في `/api/v1/health/modules` (نفس الـ output)
- ✅ لا تغيير في `health_urls.py`

## التحقق
```bash
pytest apps/platform_core/tests apps/tenancy/tests apps/evidence/tests -v
curl http://localhost:8000/api/v1/health/modules | jq .
```

## معايير القبول
- [ ] 13 ملف `health.py` بسطرين فقط
- [ ] نفس JSON response في كل الـ modules
- [ ] `manifest.py` لا يزال يشير إلى `module.health` الصحيح
- [ ] لا حاجة لتعديل `health_urls.py`

## المخاطر
🟢 **منخفضة** — استبدال ميكانيكي، ناتج متطابق
