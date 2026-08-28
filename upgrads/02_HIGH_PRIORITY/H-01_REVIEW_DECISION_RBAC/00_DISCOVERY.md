# H-01: Fix ReviewDecisionCreateView RBAC

## Discovery

### Problem
`backend/apps/reviews/api/views.py:71-90` — `ReviewDecisionCreateView` does not specify `required_roles`, allowing regular employees to create Review Decisions.

### Evidence
```python
class ReviewDecisionCreateView(TenantAPIView):
    # ❌ No required_roles

    def post(self, request):
        # ...
```

### Impact
- A01 Broken Access Control
- Employees can approve/reject evidence
- Review workflow breach

### Fix
```python
class ReviewDecisionCreateView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)  # ✅
```

### Acceptance Standards
- AC-1: Regular employee gets 403
- AC-2: Monitor can create decisions
- AC-3: Owner can create decisions
- AC-4: test_employee_cannot_create_review_decision passes

### Required Tests
```python
def test_employee_cannot_create_review_decision(self):
    # Setup employee
    # POST /api/v1/reviews/decisions/
    # Assert 403

def test_monitor_can_create_review_decision(self):
    # Setup monitor
    # POST /api/v1/reviews/decisions/
    # Assert 201

def test_owner_can_create_review_decision(self):
    # Setup owner
    # POST /api/v1/reviews/decisions/
    # Assert 201
```

### References
- [REQUIREMENTS_BASELINE.md: "Monitor authority"](../../../docs/REQUIREMENTS_BASELINE.md)
- [ARCHITECTURE_BASELINE.md: "monitor workflow"](../../../docs/ARCHITECTURE_BASELINE.md)
