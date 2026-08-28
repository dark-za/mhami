# BE-01: Goal and Plan

## SMART Goal

> Within **1 week**, every `TenantAPIView` subclass in `apps/` declares
> `required_roles` (a tuple of `CompanyRole` values), and
> `scripts/ci/audit_required_roles.py` exits 0 on a clean tree and
> exits 1 on any missing or improperly empty role tuple. The CI job
> `rbac-audit` runs on every PR.

## Detailed Acceptance Standards

### Standard 1: Per-view role matrix

Every `TenantAPIView` declares one of:

| Form | Meaning |
|---|---|
| `required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)` | Allow Owner and Monitor |
| `required_roles = (CompanyRole.OWNER,)` | Owner only |
| `required_roles = ()` + `# public` comment on the line above | All authenticated users (must be intentional) |
| `required_roles = ()` (no comment) | **Rejected by the audit** |

The audit script's exit code is:

- `0` if every view is OK
- `1` if any view is missing `required_roles`
- `1` if any view has `required_roles = ()` without `# public`

### Standard 2: Audit script implementation

```python
# backend/scripts/ci/audit_required_roles.py
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
            isinstance(b, ast.Name) and b.id == "TenantAPIView"
            for b in node.bases
        ) and not any(
            isinstance(b, ast.Attribute) and b.attr == "TenantAPIView"
            for b in node.bases
        ):
            continue
        has_roles = False
        roles_value: ast.Tuple | None = None
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if (
                        isinstance(tgt, ast.Name)
                        and tgt.id == "required_roles"
                    ):
                        has_roles = True
                        if isinstance(stmt.value, ast.Tuple):
                            roles_value = stmt.value
        if not has_roles:
            errors.append(f"{path}:{node.lineno} {node.name} missing required_roles")
            continue
        if roles_value is not None and not roles_value.elts:
            # empty tuple — must have # public comment on the line above
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

### Standard 3: CI job

`.github/workflows/ci.yml` has a `rbac-audit` job that runs the script and fails the build on any gap.

### Standard 4: Threat model mapping

`docs/SECURITY_THREAT_MODEL.md` adds a row mapping A01 Broken Access Control → `required_roles` + audit script.

---

## Detailed Implementation Plan

### Day 1 — Audit script

- [ ] Implement `scripts/ci/audit_required_roles.py`.
- [ ] Run the script; collect the gap list.
- [ ] File one tracking issue per `apps/*` directory.

### Day 2-4 — Add `required_roles`

- [ ] `apps/reviews/api/views.py` — already has H-01/H-02 fixes; double-check.
- [ ] `apps/evidence/api/views.py` — add `required_roles` per endpoint.
- [ ] `apps/tasks/api/views.py` — add `required_roles` per endpoint.
- [ ] `apps/exports/api/views.py`, `apps/backups/api/views.py`, `apps/tenancy/api/views.py`, etc.

### Day 5 — CI + docs

- [ ] Add `rbac-audit` job to `.github/workflows/ci.yml`.
- [ ] Update `docs/SECURITY_THREAT_MODEL.md`.
- [ ] Update `CHANGELOG.md`.

---

## Dependency Graph

```
audit script (Day 1)
    ↓
gap list
    ↓
add required_roles to every view (Day 2-4)
    ↓
audit script exits 0
    ↓
CI job (Day 5)
    ↓
docs
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Audit script runs and reports the gap | Backend |
| CP-2 | Every `TenantAPIView` declares `required_roles` | Backend |
| CP-3 | CI job green | DevOps |
| CP-4 | Threat model updated | Security Lead |
| CP-5 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If a view legitimately needs an empty role tuple → add `# public` comment; do not remove the audit.
- If the audit script is too slow → switch to a `pyproject.toml` marker; do not skip the audit.
