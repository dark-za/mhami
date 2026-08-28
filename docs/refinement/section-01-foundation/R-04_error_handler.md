# R-04: توحيد معالجة أخطاء API

## الهدف
كل view فيه نفس النمط:
```python
try:
    service.do(...)
except Exception as exc:
    raise _service_error(exc) from exc
```

## الوضع الحالي
~25 view فيها helper محلي:
```python
def _service_error(exc: Exception) -> PlatformAPIException:
    return PlatformAPIException(str(exc))
```

## التغيير

### 1. تحسين `platform_core/errors.py`
```python
# filepath: backend/apps/platform_core/errors.py
class PlatformAPIException(APIException):
    status_code = 400
    default_code = "CORE-ERROR-001"
    default_detail = "This action cannot be performed."

# إضافة decorator بدل الـ try/except المكرر
from functools import wraps
def platform_service_call(view_method):
    """يلتف تلقائياً حول أي Exception خدمة ويرفع PlatformAPIException."""
    @wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        try:
            return view_method(self, request, *args, **kwargs)
        except PlatformAPIException:
            raise
        except (ValueError, KeyError, TypeError) as exc:
            raise PlatformAPIException(str(exc)) from exc
        except Exception as exc:
            # خطأ غير متوقع → لا تكشف التفاصيل
            raise PlatformAPIException("The action could not be completed.") from exc
    return wrapper
```

### 2. تحويل views
```python
# قبل
class CaptureSessionView(TenantAPIView):
    def post(self, request):
        ...
        try:
            session = create_capture_session(...)
        except Exception as exc:
            raise _service_error(exc) from exc

# بعد
class CaptureSessionView(TenantAPIView):
    @platform_service_call
    def post(self, request):
        ...
        session = create_capture_session(...)
```

## الأثر
- ⬇️ **−250 سطر** (إزالة try/except و helper)
- ✅ **+أمان**: الأخطاء غير المتوقعة لا تكشف تفاصيل حساسة
- ✅ **DRY**: نقطة واحدة لمعالجة أخطاء الخدمات

## التحقق
```bash
pytest apps/evidence/tests apps/tasks/tests apps/reviews/tests -v
# اختبار: Exception غير متوقع → 400 عام
```

## معايير القبول
- [ ] لا `_service_error()` helper محلي في أي view
- [ ] كل view method تستخدم `@platform_service_call` (اختياري لكن موصى به)
- [ ] logging موحّد للخطأ الداخلي (`exc_info=True`)

## المخاطر
🟡 **متوسطة** — يجب التأكد أن الأخطاء المُتوقعة تُرفع كما هي (مثال: `InvalidCompanyLifecycleTransition`)

## احتياطات
- اجعل `PlatformAPIException` و subclasses تمرّ مباشرة دون تغليف
- سجّل `exc_info=True` للأخطاء غير المتوقعة فقط
- لا تغيّر سلوك الـ DRF default exception handler
