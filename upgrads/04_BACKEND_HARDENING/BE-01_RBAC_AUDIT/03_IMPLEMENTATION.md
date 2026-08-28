# BE-01: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. The audit script is the single source of truth for whether a view is correctly guarded.

## Step 1: Audit script

### 1.1 New file: `backend/scripts/ci/audit_required_roles.py`

```python
"""Audit every TenantAPIView subclass for a required_roles declaration.

Exits 0 on a clean tree, 1 on any missing or improperly empty role tuple.
"""
from __future__ import annotations

import ast
import pathlib
import sys

REQUIRED_FILES = list(pathlib.Path("apps").rglob("views.py"))


def check_file(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text())
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(
            isinstance(b, ast.Name) and b.id == "TenantAPIView" for b in node.bases
        ) and not any(
            isinstance(b, ast.Attribute) and b.attr == "TenantAPIView" for b in node.bases
        ):
            continue
        has_roles = False
        roles_value: ast.Tuple | None = None
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "required_roles":
                        has_roles = True
                        if isinstance(stmt.value, ast.Tuple):
                            roles_value = stmt.value
        if not has_roles:
            errors.append(f"{path}:{node.lineno} {node.name} missing required_roles")
            continue
        if roles_value is not None and not roles_value.elts:
            src = path.read_text().splitlines()
            if node.lineno - 1 < 0 or "# public" not in src[node.lineno - 1]:
                errors.append(
                    f"{path}:{node.lineno} {node.name} empty required_roles without # public"
                )
    return errors


def main() -> int:
    errs: list[str] = []
    for f in REQUIRED_FILES:
        errs.extend(check_file(f))
    if errs:
        for e in errs:
            print(f"MISSING: {e}")
        return 1
    print(f"OK: {len(REQUIRED_FILES)} files audited, 0 gaps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 1.2 Verify

```bash
cd backend
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Today: 1 (gaps). After all fixes: 0.
```

---

## Step 2: Add `required_roles` to every view

### 2.1 Pattern

```python
# Before
class MyView(TenantAPIView):
    serializer_class = MySerializer
    def post(self, request): ...

# After
class MyView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)
    serializer_class = MySerializer
    def post(self, request): ...
```

### 2.2 The role matrix

| Endpoint pattern | Roles |
|---|---|
| Owner-only configuration (company settings, branch CRUD, AI provider, backup run) | `(CompanyRole.OWNER,)` |
| Owner + Monitor (review decisions, exports, audit log) | `(CompanyRole.OWNER, CompanyRole.MONITOR)` |
| Owner + Monitor + Supervisor (review queue, evidence list) | `(CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.SUPERVISOR)` |
| All authenticated employees (task list, evidence upload) | `# public` + `required_roles = ()` |
| Authenticated (login, bootstrap) | `# public` + `required_roles = ()` |

### 2.3 Files to update

| File | Action |
|---|---|
| `apps/reviews/api/views.py` | already has H-01/H-02 fixes; verify |
| `apps/evidence/api/views.py` | add `required_roles` per endpoint |
| `apps/tasks/api/views.py` | add `required_roles` per endpoint |
| `apps/exports/api/views.py` | add `required_roles` per endpoint |
| `apps/backups/api/views.py` | add `required_roles` per endpoint |
| `apps/tenancy/api/views.py` | add `required_roles` per endpoint |
| `apps/organizations/api/views.py` | add `required_roles` per endpoint |
| `apps/identity/api/views.py` | add `required_roles` per endpoint |
| `apps/notifications/api/views.py` | add `required_roles` per endpoint |
| `apps/ai_gateway/api/views.py` | add `required_roles` per endpoint |
| `apps/connector_control/api/views.py` | add `required_roles` per endpoint |
| `apps/pilot/api/views.py` | add `required_roles` per endpoint |

**Verify after each file:**

```bash
cd backend
python scripts/ci/audit_required_roles.py 2>&1 | Select-String -Pattern "apps/$(basename $(dirname $file))"
# Expected: 0 MISSING lines
```

---

## Step 3: CI job

### 3.1 Update `.github/workflows/ci.yml`

```yaml
  rbac-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Audit required_roles
        run: |
          cd backend
          pip install -r requirements.txt
          python scripts/ci/audit_required_roles.py
```

**Verify:**
```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "rbac-audit"
# Expected: 1+ match
```

---

## Step 4: Threat model update

Append to `docs/SECURITY_THREAT_MODEL.md`:

```markdown
| A01 Broken Access Control | `required_roles` on every TenantAPIView + audit script | backend |
```

**Verify:**
```bash
Select-String -Path docs\SECURITY_THREAT_MODEL.md -Pattern "required_roles"
# Expected: 1+ match
```

---

## Step 5: Documentation

1. Update `docs/SECURITY_THREAT_MODEL.md` (A01 control).
2. Update `CHANGELOG.md` with a `BE-01` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Audit script exists | `Test-Path backend\scripts\ci\audit_required_roles.py` | True |
| Audit script exits 0 | `python scripts/ci/audit_required_roles.py` | 0 |
| Every `TenantAPIView` covered | audit script reports 0 MISSING | 0 |
| CI job | `grep rbac-audit .github/workflows/ci.yml` | match |
| Threat model | `grep required_roles docs/SECURITY_THREAT_MODEL.md` | match |

---

## Rollback

```bash
git revert <be01-commit-sha>
cd backend
python scripts/ci/audit_required_roles.py
# Expected: non-zero (the audit will flag the reverted views)
```
