# C-03: Verification Commands

## Phase 1: Proving the Problem (Pre-Fix)

### Command 1.1: Run IDOR test before fix

```bash
cd backend
pytest apps/organizations/tests/test_idor_weeklyshift.py::TestWeeklyShiftIDOR::test_cross_company_branch_rejected -v
```

**Expected output:** `FAILED` (vulnerability exists).

### Command 1.2: Confirm absence of validate method

```bash
grep -A 5 "class WeeklyShiftCreateSerializer" backend/apps/organizations/serializers.py
```

**Expected output:** No `def validate(`.

### Command 1.3: Confirm absence of cross-company check

```bash
grep -n "company_id" backend/apps/organizations/api/views.py | head
```

**Expected output:** only in `context.company`, not in `validated_data`.

---

## Phase 2: Verifying the Solution (Post-Fix)

### Command 2.1: Run IDOR tests

```bash
cd backend
pytest apps/organizations/tests/test_idor_weeklyshift.py -v
```

**Expected output:** `4 passed`.

### Command 2.2: Run all organization tests

```bash
pytest apps/organizations/ -v
```

**Expected output:** all tests pass, no regression.

### Command 2.3: Verify validate method exists

```bash
grep "def validate" backend/apps/organizations/serializers.py
```

**Expected output:** `def validate(self, attrs):`.

### Command 2.4: Verify audit event

```bash
pytest apps/organizations/tests/test_idor_weeklyshift.py::TestWeeklyShiftIDOR::test_cross_company_branch_rejected -v -s
```

**Expected output:** Audit event `WEEKLY_SHIFT_REJECTED_IDOR` is logged (if added).
