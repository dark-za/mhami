# BE-01: Verification Commands

> **Instructions:** Run the baseline (Phase 1) before the change, then the post-fix (Phase 2) to confirm every `TenantAPIView` declares `required_roles` and the CI script catches the gap.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Count `TenantAPIView` subclasses

```bash
Select-String -Path backend\apps -Pattern "TenantAPIView" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
# Expected: 60+
```

### Command 1.2 — Count views declaring `required_roles`

```bash
Select-String -Path backend\apps -Pattern "required_roles" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
# Expected today: < 60 (some views are missing)
```

### Command 1.3 — Audit script does not exist

```bash
Test-Path backend\scripts\ci\audit_required_roles.py
# Expected: False
```

### Command 1.4 — CI job missing

```bash
Select-String -Path .github\workflows\*.yml -Pattern "rbac-audit"
# Expected: 0 matches
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — Audit script exists

```bash
Test-Path backend\scripts\ci\audit_required_roles.py
# Expected: True
```

### Command 2.2 — Audit script reports zero gaps

```bash
cd backend
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected: 0 (success)
```

### Command 2.3 — Every `TenantAPIView` has `required_roles`

```bash
# The script reports per-view; expect every line to start with "OK"
python scripts/ci/audit_required_roles.py 2>&1 | Select-String -Pattern "MISSING"
# Expected: 0 matches
```

### Command 2.4 — CI job green

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "rbac-audit"
# Expected: 1+ match
```

### Command 2.5 — Threat model updated

```bash
Select-String -Path docs\SECURITY_THREAT_MODEL.md -Pattern "rbac-audit"
# Expected: 1 match
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Existing tests still pass

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```

### Command 3.2 — A view without `required_roles` triggers the audit

```bash
# Create a temporary view missing the attribute
echo 'class TempView(TenantAPIView):
    pass' >> backend/apps/reviews/api/views.py
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected: 1 (failure)
# Revert
git checkout backend/apps/reviews/api/views.py
```

### Command 3.3 — Empty tuple is allowed only with `# public` comment

```bash
# Add a view with required_roles = () and no comment
echo 'class TempPublicView(TenantAPIView):
    required_roles = ()' >> backend/apps/reviews/api/views.py
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected: 1 (failure: empty tuple without # public)
git checkout backend/apps/reviews/api/views.py
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 / 1.4 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 green
- ✅ Command 3.1 no regression
- ✅ Command 3.2 / 3.3 the audit catches both kinds of mistake
