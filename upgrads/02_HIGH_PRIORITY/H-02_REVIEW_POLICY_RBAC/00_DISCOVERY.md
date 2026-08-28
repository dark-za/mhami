# H-02: Fix ReviewPolicyView RBAC

## Discovery

### Problem
`backend/apps/reviews/api/views.py:50-69` — `ReviewPolicyView.patch` does not specify `required_roles`, allowing any authenticated user to attempt modifying the policy. (OWNER check happens inside the function, but defense in depth is preferred.)

### Evidence
```python
class ReviewPolicyView(TenantAPIView):
    # ❌ No required_roles at class level

    def patch(self, request):
        company = self.get_tenant().company
        membership = CompanyMembership.objects.filter(...).only("role").first()
        if membership is None or membership.role != CompanyRole.OWNER:
            raise PlatformAPIException("Policy changes require owner access.")
        # ...
```

### Impact
- A01 Broken Access Control
- Relies on logic inside the function instead of class-level

### Fix
```python
class ReviewPolicyView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)  # ✅
```

### Acceptance Standards
- AC-1: Employee and Monitor get 403 early
- AC-2: Owner only can PATCH
- AC-3: No regression in GET

### Required Tests
- test_employee_cannot_patch_policy
- test_monitor_cannot_patch_policy
- test_owner_can_patch_policy
