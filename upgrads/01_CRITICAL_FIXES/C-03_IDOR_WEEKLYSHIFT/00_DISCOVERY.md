# C-03: Fix IDOR in WeeklyShift (Cross-Tenant Data Injection)

## 1. Discovery Summary

### Current State

**Problem:** `WeeklyShiftCreateSerializer` accepts `branch_id` and `user_id` as raw UUID values, and `WeeklyShiftsView.post` uses them in `WeeklyShift.objects.create(company=company, **serializer.validated_data)` without verifying that these IDs belong to the current company.

**Guide:**

`backend/apps/organizations/serializers.py:23-30`:
```python
class WeeklyShiftCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    # ❌ No validate() method
```

`backend/apps/organizations/api/views.py:117-125`:
```python
serializer = WeeklyShiftCreateSerializer(data=request.data)
serializer.is_valid(raise_exception=True)
shift = WeeklyShift.objects.create(company=company, **serializer.validated_data)
# ❌ validated_data contains branch_id and user_id as raw values
# ❌ No check that branch belongs to company
```

### Exploit Scenario

1. Owner of company A logs in
2. Sends POST `/api/v1/organizations/weekly-shifts/` with:
   ```json
   {
     "branch_id": "<branch-id-of-company-B>",
     "user_id": "<user-id-of-company-B>",
     "weekday": 0,
     "start_time": "09:00",
     "end_time": "17:00"
   }
   ```
3. The system creates a `WeeklyShift` for `company=A` but with `branch=B-branch` and `user=B-user`
4. **Tenant isolation breach (A01)**

### Reproducible Evidence

```python
# in test conftest
def test_idor_weekly_shift():
    company_a = make_company(code="a")
    company_b = make_company(code="b")
    branch_b = make_branch(company=company_b, code="b1")
    user_b = make_user(login_id="u_b")

    client = make_client(force_login(company_a.owner))

    # IDOR attempt
    response = client.post("/api/v1/organizations/weekly-shifts/", {
        "branch_id": str(branch_b.id),
        "user_id": str(user_b.id),
        "weekday": 0,
        "start_time": "09:00",
        "end_time": "17:00",
    })

    # ❌ Currently passes with 201
    # ✅ must fail with 403
    assert response.status_code == 403
```

### Impact

| Dimension | Impact |
|---|---|
| Security | A01 Broken Access Control - Critical |
| Functional | A company owner can write to another company's records |
| Compliance | Violates [REQUIREMENTS_BASELINE.md Tenant Isolation] |
| Severity | Critical exploitable vulnerability |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Validation in Serializer | none | validate() method |
| Branch.company check | No | Yes |
| User.company check | No | Yes |
| IDOR test | none | Exists and runs |
| Tenant Isolation | Breached | Hardened |

---

## 3. Goal

> Within **3 days**, add `validate()` method in `WeeklyShiftCreateSerializer` to verify that `branch_id` and `user_id` belong to the current company, and add comprehensive IDOR Tests.

### Acceptance Standards

1. **AC-1:** IDOR attempt is rejected with an authorization-safe 403/404.
2. **AC-2:** Valid attempts require branch, user, and active branch membership in the current company.
3. **AC-3:** Weekday and time invariants hold; zero-length, reversed, duplicate, and overlapping shifts follow an explicit product policy.
4. **AC-4:** Scheduler tests prove that a shift cannot assign a user outside its active branch scope.
5. **AC-5:** Tests cover cross-company branch/user, expired membership, inactive branch, overlap, and concurrent creation.
6. **AC-6:** No regression in existing features, with an approved audit policy for rejected authorization attempts.

---

## 4. Sub-tasks

- [ ] Add `validate()` method in `WeeklyShiftCreateSerializer`
- [ ] Add helper `_validate_company_owned` in `apps/tenancy/access.py`
- [ ] Add `test_idor_weekly_shift` and other tests
- [ ] Record audit event on validation failure
- [ ] Run `pytest apps/organizations/` and ensure no regression
- [ ] Update `docs/SECURITY_THREAT_MODEL.md` (add TM-XXX)
