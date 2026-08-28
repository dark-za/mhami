# BE-01: Test Strategy

> **Rule:** every check in this file must pass on a real backend. The audit script is the gate.

## 1. Unit Tests

Not applicable — the audit script is itself the test.

## 2. Integration Tests

### 2.1 Audit script exits 0

```bash
cd backend
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### 2.2 Audit script reports file count

```bash
cd backend
python scripts/ci/audit_required_roles.py
# Expected: "OK: N files audited, 0 gaps"
```

### 2.3 Audit script catches a missing `required_roles`

```bash
# Add a temp view
echo 'class TempView(TenantAPIView):
    pass' >> backend/apps/reviews/api/views.py
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected: 1
git checkout backend/apps/reviews/api/views.py
```

### 2.4 Audit script catches empty `required_roles` without `# public`

```bash
echo 'class TempPublicView(TenantAPIView):
    required_roles = ()' >> backend/apps/reviews/api/views.py
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected: 1
git checkout backend/apps/reviews/api/views.py
```

### 2.5 Audit script accepts empty `required_roles` with `# public`

```bash
cat >> backend/apps/reviews/api/views.py <<'PY'
# public
class TempPublicView(TenantAPIView):
    required_roles = ()
PY
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected: 0
git checkout backend/apps/reviews/api/views.py
```

---

## 3. End-to-End Tests

### 3.1 Each `TenantAPIView` rejects an employee when role is not in `required_roles`

```bash
cd backend
pytest apps/reviews/tests/test_role_enforcement.py -v
# Expected: every test green
```

### 3.2 CI `rbac-audit` job

```bash
Get-Content .github/workflows/ci.yml | Select-String -Pattern "rbac-audit"
# Expected: 1+ match
```

### 3.3 Threat model

```bash
Select-String -Path docs/SECURITY_THREAT_MODEL.md -Pattern "required_roles"
# Expected: 1+ match
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| Audit script | 1 | exit 0 |
| Catch missing | 1 | exit 1 |
| Catch empty w/o comment | 1 | exit 1 |
| Accept empty w/ comment | 1 | exit 0 |
| Existing tests | N | green |
| CI job | 1 | present |
| Threat model | 1 | updated |

---

## 5. Run Tests

### 5.1 Local

```bash
cd backend
python scripts/ci/audit_required_roles.py
pytest -m "not slow" -q
```

### 5.2 CI

The `rbac-audit` job runs on every PR. The full pytest runs in the existing `backend` job.

### 5.3 Failure simulation

| Scenario | Expected |
|---|---|
| Add a view with no `required_roles` | exit 1 |
| Add a view with empty `required_roles` and no `# public` | exit 1 |
| Add a view with empty `required_roles` and `# public` | exit 0 |

---

## 6. Cross-links

- [upgrads/02_HIGH_PRIORITY/H-01_REVIEW_DECISION_RBAC](../../02_HIGH_PRIORITY/H-01_REVIEW_DECISION_RBAC/00_DISCOVERY.md)
- [upgrads/02_HIGH_PRIORITY/H-02_REVIEW_POLICY_RBAC](../../02_HIGH_PRIORITY/H-02_REVIEW_POLICY_RBAC/00_DISCOVERY.md)
- [upgrads/04_BACKEND_HARDENING/BE-02_SERIALIZER_VALIDATION](..)
