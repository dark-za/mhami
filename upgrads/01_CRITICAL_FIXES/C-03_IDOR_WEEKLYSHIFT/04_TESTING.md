# C-03: Test Strategy

## 1. Unit Tests

**File:** `backend/apps/organizations/tests/test_idor_weeklyshift.py`

4 main tests:
1. `test_cross_company_branch_rejected` - branch belonging to another company
2. `test_cross_company_user_rejected` - user belonging to another company
3. `test_valid_shift_accepted` - Valid case
4. `test_inactive_branch_membership_rejected` - user without active membership

## 2. Integration Tests

```python
def test_idor_with_session_company_mismatch():
    """Owner logs into company A but tries to use company B's branch."""
    # Pre-fix: passes (vulnerable)
    # Post-fix: 403
```

## 3. Regression Tests

```bash
pytest apps/organizations/tests/ -v
```

**Expected:** 100% pass, no regression.

## 4. Success Criteria

| Test | Result |
|---|---|
| 4 IDOR tests | passed |
| existing tests | passed |
| Audit events | logged |
