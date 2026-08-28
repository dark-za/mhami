# R-09: اختبارات مُبسّطة عبر conftest مشترك

> **Status:** ✅ Completed (2026-08-28) — 5 factories + HTTP helper + 7 smoke tests. لا regressions.

## الهدف
كل `apps/*/tests/` فيها setup متكرر:
```python
def test_xxx(self):
    user = User.objects.create_user(...)
    company = Company.objects.create(...)
    membership = CompanyMembership.objects.create(...)
    # 10 أسطر setup قبل كل اختبار
```

## الوضع قبل (audit)
| النمط | عدد مرات التكرار |
|---|---|
| `User.objects.create_user` | 48 |
| `Company.objects.create` | 31 |
| `Branch.objects.create` | 22 |
| `CompanyMembership.objects.create` | 37 |
| helper functions خاصة (`def _context`, `def create_*`) | 6 |

## التغيير

### 1. `backend/conftest.py` factories موحدة (208 سطر)
```python
# filepath: backend/conftest.py

@pytest.fixture
def make_user(db) -> Callable[..., User]:
    """Factory: User"""
    def _factory(*, login_id=None, password="TestPass123!", **kwargs):
        return User.objects.create_user(
            login_id=login_id or _next_user_login(),
            password=password,
            display_name=kwargs.pop("display_name", None) or "Test User",
            **kwargs,
        )
    return _factory

@pytest.fixture
def make_company(db, make_user):
    """Factory: Company with auto-created owner"""
    def _factory(*, code=None, status="active", owner=None, industry="other",
                 trial_ends_at=None, **kwargs):
        owner = owner or make_user(login_id=_next_user_login(prefix="owner"))
        return Company.objects.create(
            name=kwargs.pop("name", f"Test Company {uuid4().hex[:6]}"),
            code=code or _next_company_code(),
            industry=industry,
            owner=owner,
            status=status,
            trial_ends_at=trial_ends_at or timezone.make_aware(datetime(2030, 1, 1, 0, 0)),
            **kwargs,
        )
    return _factory

@pytest.fixture
def make_branch(db, make_company):
    """Factory: Branch with company auto-created if not provided"""
    ...

@pytest.fixture
def make_membership(db, make_user, make_company):
    """Factory: CompanyMembership defaults to OWNER role"""
    ...

@pytest.fixture
def force_login_company(db, make_company):
    """HTTP helper: combines Client() + force_login + session['company_id']"""
    def _factory(user, company):
        client = Client()
        client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        session = client.session
        session["company_id"] = str(company.id)
        session.save()
        return client
    return _factory
```

### 2. `tests/test_factories_smoke.py` (7 tests جديدة)
اختبارات smoke تتأكد من أن كل factory ينتج instances صحيحة. هذه العقد المرجعي للـ factories.

```python
def test_make_user_returns_user_with_login_id(make_user): ...
def test_make_user_auto_increments_login_id(make_user): ...
def test_make_company_creates_owner_user(make_user, make_company): ...
def test_make_company_reuses_existing_owner(make_user, make_company): ...
def test_make_branch_creates_branch_under_company(make_company, make_branch): ...
def test_make_membership_defaults_to_owner_role(...): ...
def test_force_login_company_creates_authenticated_client(...): ...
```

## النمط الجديد في الـ tests (مثال)
```python
# قبل (R-09 قبل)
def test_ai_provider_setup(make_user, make_company, make_branch, make_membership):
    owner = make_user(login_id="ai-owner", password="password123", display_name="Owner")
    monitor = make_user(login_id="ai-monitor", password="password123", display_name="Monitor")
    company = make_company(
        name="AI Co", code="ai-co", industry="other", owner=owner,
        trial_ends_at=timezone.make_aware(datetime(2030, 1, 1, 0, 0)),
    )
    make_membership(company=company, user=owner, role=CompanyRole.OWNER)
    make_membership(company=company, user=monitor, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, name="Main", code="main",
                         timezone="UTC", operational_day_cutoff=time(6, 0))
    # الاختبار الفعلي يبدأ هنا

# بعد (R-09b — في commit لاحق)
def test_ai_provider_setup(make_user, make_company, make_branch, make_membership):
    owner = make_user(login_id="ai-owner", display_name="Owner")
    monitor = make_user(login_id="ai-monitor", display_name="Monitor")
    company = make_company(name="AI Co", code="ai-co", owner=owner)
    make_membership(company=company, user=owner, role=CompanyRole.OWNER)
    make_membership(company=company, user=monitor, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, code="main", name="Main")
    # 7 أسطر بدلاً من 13 سطر
```

## الأثر الفعلي
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `conftest.py` (root) | 6 سطور | 208 سطور | +202 (factories + docs) |
| عدد الـ factories | 0 | 5 | +5 |
| عدد smoke tests | 0 | 7 | +7 |
| Tests passing | 79 | 86 | +7 (الـ smoke) |
| Tests failing (pre-existing) | 5 | 5 | 0 regressions |
| conftest.py محلي في apps | 0 | 0 | لا تغيير (لم يُضف أي) |

## التحقق
```bash
$env:DJANGO_SETTINGS_MODULE="config.settings.test"
cd backend
python -m pytest tests/test_factories_smoke.py -v   # 7/7 passed
python -m pytest apps/ tests/ -q                      # 86 passed, 5 pre-existing failures
```

## معايير القبول
- [x] الـ 5 factories الأساسية متاحة على مستوى الـ root conftest
- [x] smoke tests تتحقق من كل factory
- [x] لا regression في عدد الـ tests passing
- [x] `force_login_company` يقلص setup المتعلق بـ session إلى سطر واحد

## المخاطر
🟢 **منخفضة** — refactor للاختبارات، لا يمس كود الإنتاج. الـ factories اختيارية (الـ tests القديمة تستمر في العمل).

## ملاحظات
- ❌ **لم يتم** تحديث الـ tests الموجودة لاستخدام factories. هذا متعمَّد:
  - 26 ملف test سيتطلب كل منها مراجعة يدوية للتأكد من أن الـ default values مناسبة
  - الـ factories متاحة الآن للمطورين الجدد وأي test جديد
  - R-09b (commit مستقبلي) سيهاجر تدريجياً
- ✅ الـ factories تستخدم module-level counters (`_user_counter`, `_company_counter`, `_branch_counter`) لضمان uniqueness عبر الـ tests
- ✅ كل factory يمر عبر `db` fixture فلا حاجة لـ `pytestmark = pytest.mark.django_db` يدوياً (لكنه لا يزال مطلوباً للـ tests الفعلية)

## التحويلات المستقبلية (R-09b)
عند البدء بالهجرة:
1. اختر test بسيط (مثل `test_company_model.py`)
2. استبدل `User.objects.create_user(...)` بـ `make_user(login_id=...)`
3. شغّل pytest للتأكد من نفس النتيجة
4. استمر مع باقي الـ tests الـ 25 الأخرى
