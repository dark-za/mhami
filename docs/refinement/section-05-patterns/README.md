# القسم الخامس: أنماط متقدمة (Advanced Patterns)

> **المراحل:** R-11 → R-12
> **المدة المقدرة:** 2-3 أيام
> **الأثر:** ~−400 سطر + أمان أعلى
> **المخاطرة:** 🟡 متوسطة

## فلسفة القسم

الأنماط **المتقدمة** التي تربط الـ modules ببعضها:
- **Outbox events**: العقد الموحّد للأحداث الصادرة
- **Tenant QuerySets**: كل model tenant-scoped يمر عبر pattern موحّد

## القاعدة الذهبية

> **events موحّدة = استبدال سهل للمستهلكين، tenant querysets = صفر ثغرات IDOR**

---

## المراحل بالترتيب

| # | المرحلة | الأثر | المخاطرة | المدة |
|---|---|---|---|---|
| **R-11** | [Outbox events موحّدة](R-11_outbox_events.md) | −150 سطر | 🟡 | 4 ساعات |
| **R-12** | [Tenant QuerySets](R-12_tenant_querysets.md) | −250 سطر | 🟡 | 6 ساعات |

**المجموع:** ~−400 سطر + أمان أعلى، ~10 ساعات عمل

---

## 🎯 معايير إكمال القسم

### R-11
- [ ] كل event يمر عبر `OutboxEvent` dataclass
- [ ] كل emit يمر عبر `apps.platform_core.outbox.emit`
- [ ] `transaction.on_commit` مُعالَج (events تُكتب في commit)
- [ ] اختبار: rollback → event لا يُكتب
- [ ] اختبار: re-run consumer → idempotency

### R-12
- [ ] كل model tenant-scoped يستخدم `TenantManager`
- [ ] كل view يستخدم `.for_company()` أو `.for_company_and_branches()`
- [ ] لا استخدام مباشر لـ `Model.objects.filter(company=...)` في views
- [ ] tenant isolation tests تبقى خضراء

---

## 📊 مقاييس Baseline

```
backend/apps/notifications/services.py: outbox events مكررة
backend/apps/*/api/views.py:           ~30+ view مع filter(company=...) مكرر
                                       13 model tenant-scoped يدوياً
```

## 📊 مقاييس مستهدفة

```
backend/apps/platform_core/outbox.py:  عقد موحّد + emit function
backend/apps/platform_core/querysets.py: TenantQuerySet + TenantManager
backend/apps/*/models.py:             كل model tenant-scoped بـ TenantManager
backend/apps/*/api/views.py:           أنظف بـ for_company/for_company_and_branches
```

---

## 🔗 العلاقات

```
R-11 و R-12 مستقلان
```

- R-11 (events) يمس الـ outbox و الـ consumers
- R-12 (querysets) يمس الـ models و الـ views
- يمكن تنفيذهما بالتوازي على modules مختلفة

---

## ⚠️ احتياطات القسم

### R-11
- اختبر scenarios: rollback → event لا يُكتب ✓
- اختبر scenarios: re-run consumer → idempotency ✓
- لا تغيّر `OutboxEvent` model في `notifications` — فقط أضف helper

### R-12
- ابدأ بـ `EvidenceItem` و `TaskInstance` فقط
- اختبارات tenant isolation يجب أن تبقى خضراء
- لا تحذف `company=...` filter القديم حتى تنتهي كل الـ views
- **قد يكشف bugs موجودة** (queries بدون scope) — هذا مطلوب، وثّقه

---

## 🚀 الخطوة التالية بعد إكمال القسم

عند اكتمال R-11 → R-12، انتقل إلى **[القسم السادس: الحوكمة](../section-06-governance/README.md)**
