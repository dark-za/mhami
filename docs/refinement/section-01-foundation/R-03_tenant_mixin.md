# R-03: قاعدة TenantContext كـ Mixin

## الهدف
كل `APIView` يحقن `tenant_context(request)` بنفس الطريقة، بنفس try/except، بنفس استخراج الـ company/role/branches.

## الوضع الحالي
~30+ view في `apps/*/api/views.py` فيها:
```python
def post(self, request):
    context = tenant_context(request)  # قد يرمي PlatformPermissionException
    company = context.company
    role = context.role
    ...
```

## التغيير

### 1. إنشاء `apps/platform_core/mixins.py`
```python
# filepath: backend/apps/platform_core/mixins.py
from __future__ import annotations
from rest_framework.views import APIView
from apps.tenancy.access import tenant_context, TenantContext, require_company_user

class TenantAPIView(APIView):
    """APIView يحقن تلقائياً tenant_context ويفرض الصلاحيات."""
    
    required_roles: tuple[str, ...] = ()  # override
    require_branch: bool = True  # override
    
    def get_tenant(self) -> TenantContext:
        if not hasattr(self.request, "_cached_tenant"):
            self.request._cached_tenant = tenant_context(self.request)
        return self.request._cached_tenant
    
    def check_tenant(self) -> TenantContext:
        context = self.get_tenant()
        if self.required_roles:
            context.require_roles(*self.required_roles)
        return context
```

### 2. تحويل views
```python
# قبل
class CaptureSessionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        company = tenant_context(request).company
        ...

# بعد
class CaptureSessionView(TenantAPIView):
    permission_classes = [IsAuthenticated]
    required_roles = ("EMPLOYEE", "OWNER", "MONITOR")
    def post(self, request):
        company = self.check_tenant().company
        ...
```

## الأثر
- ⬇️ **−300 سطر** (إزالة التكرار في 30+ view)
- ✅ **+وضوح** للقارئ: الصلاحيات مُعلنة في الكلاس
- ✅ **+أمان** صريح: roles مُعلنة ومرئية

## التحقق
```bash
pytest apps/tenancy/tests/test_api.py apps/evidence/tests/test_api.py -v
```

## معايير القبول
- [ ] كل `APIView` يرث من `TenantAPIView` (30+ view)
- [ ] `required_roles` صريح في كل view
- [ ] لا regression في permission tests

## المخاطر
🟡 **متوسطة** — يلمس 30+ ملف. تنفيذ على دفعات:
1. phase-A: `tenancy/views.py` فقط
2. phase-B: `evidence/views.py`, `tasks/views.py`
3. phase-C: الباقي

## احتياطات
- استخدم `git mv` + commits صغيرة
- لا تغيّر `tenant_context()` نفسه
- حافظ على نفس ترتيب الـ middleware
