# R-05: طبقة Services موحّدة بنمط Function-Based

## الهدف
كل module عنده `services.py` فيه functions. الهدف: توحيد النمط، إزالة الـ helper غير الضروري، توثيق الـ contract.

## الوضع الحالي
نمط متكرر في كل `services.py`:
```python
@transaction.atomic
def create_thing(...):
    obj = Thing(...)
    obj.save()
    record_audit_event(...)
    return obj
```

## التغيير

### 1. إنشاء `apps/platform_core/service_base.py`
```python
# filepath: backend/apps/platform_core/service_base.py
from __future__ import annotations
from contextlib import contextmanager
from functools import wraps
from django.db import transaction
from apps.audit.services import record_audit_event

def audited_service(*, event_type: str, target_type: str):
    """decorator يضمن atomic + audit event recording."""
    def decorator(func):
        @wraps(func)
        @transaction.atomic
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            record_audit_event(
                event_type=event_type,
                target_type=target_type,
                target_id=str(getattr(result, "id", "")),
                after=result_to_dict(result) if result else {},
            )
            return result
        return wrapper
    return decorator

def result_to_dict(obj) -> dict:
    """Helper موحّد لتحويل كائن إلى dict للأudit."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {}
```

### 2. تطبيق في `tenancy/services.py`
```python
# قبل
@transaction.atomic
def register_company(...):
    ...
    record_audit_event(event_type="tenancy.company.created", ...)
    return company, owner

# بعد
@audited_service(event_type="tenancy.company.created", target_type="Company")
def register_company(...):
    ...
    return company, owner
```

## الأثر
- ⬇️ **−400 سطر** (إزالة @transaction.atomic + record_audit_event المكرر)
- ✅ **+وضوح**: service contract واضح
- ✅ **+testability**: services قابلة للاختبار بدون mocks للـ audit

## التحقق
```bash
pytest apps/tenancy/tests apps/evidence/tests apps/tasks/tests -v
# Audit event count لم يتغير
```

## معايير القبول
- [ ] كل `@transaction.atomic` يأتي عبر `@audited_service` أو `transaction.atomic` صريح
- [ ] عدد الـ AuditEvent المُنشأ متطابق قبل/بعد
- [ ] لا تغيير في `register_audit_event` signature

## المخاطر
🟡 **متوسطة** — لمساس بالـ audit chain. يجب التحقق أن `previous_hash` و `event_hash` لا يتأثران.

## احتياطات
- اختبر audit chain integrity بعد التطبيق
- لا تغيّر معامل `previous_hash` في `record_audit_event`
- إذا كان service لا يحتاج audit (read-only)، استخدم `@transaction.atomic` عادي
