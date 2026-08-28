# BE-01: Audit required_roles on every TenantAPIView

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The codebase has 60+ `TenantAPIView` subclasses across `apps/reviews`, `apps/evidence`, `apps/exports`, `apps/backups`, `apps/tenancy`, `apps/tasks`, etc. Some declare `required_roles`; many do not. The default is "authenticated only", which means any tenant member can hit any endpoint that does not opt-in. The H-01/H-02 fixes (already done) added `required_roles` to `ReviewDecisionCreateView` and `ReviewPolicyView`, but a full audit is needed to find the rest.

**Evidence gathered:**

```bash
# 1. Count TenantAPIView subclasses
Get-ChildItem apps -Recurse -Filter views.py |
  ForEach-Object { Select-String $_ -Pattern "TenantAPIView" } |
  Measure-Object | Select-Object -ExpandProperty Count
# Expected: 60+

# 2. Find views that DO NOT declare required_roles
Select-String -Path apps/**/*.py -Pattern "class .*\(TenantAPIView\)" -List |
  ForEach-Object {
    $path = $_.Path
    $line = $_.LineNumber
    $ctx = (Get-Content $path)[$line..($line + 40)] -join "`n"
    if ($ctx -notmatch "required_roles") {
      Write-Host "MISSING: $path line $line"
    }
  }
# Expected: many hits
```

### Impact

| Dimension | Impact |
|---|---|
| Security | A low-privilege employee can hit admin-only endpoints until a guard is added. |
| Compliance | Gate-B (PDPL) requires least-privilege on every endpoint. |
| Operational | Adding a new endpoint silently inherits "no role check" until someone audits it. |

### Reproducible Evidence

```bash
# 1. The audit script lives in scripts/ci/audit_required_roles.py
python scripts/ci/audit_required_roles.py
echo "Exit code: $LASTEXITCODE"
# Expected today: non-zero (at least one view missing required_roles)
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Total `TenantAPIView` subclasses | 60+ | 60+ (no change) |
| With `required_roles` declared | ~25 (estimated) | 60+ |
| With **no** `required_roles` | ~35 (estimated) | 0 |
| CI audit script | missing | exits 1 on any gap |

---

## 3. Goal Statement

> Within **1 week**, every `TenantAPIView` subclass declares `required_roles` (a tuple of `CompanyRole` values), and a CI script (`scripts/ci/audit_required_roles.py`) fails the build if any view is missing it.

### Acceptance Criteria

1. **AC-1:** `scripts/ci/audit_required_roles.py` parses every `views.py` under `apps/`, identifies `TenantAPIView` subclasses, and reports any without `required_roles`.
2. **AC-2:** Every `TenantAPIView` declares `required_roles = (...)`.
3. **AC-3:** The CI job `rbac-audit` runs the script on every PR and fails the build on any gap.
4. **AC-4:** `apps/reviews/api/views.py` continues to use `CompanyRole.OWNER`, `CompanyRole.MONITOR` (post H-01 fix).
5. **AC-5:** `apps/reviews/api/views.py::ReviewPolicyView` continues to use `CompanyRole.OWNER` (post H-02 fix).
6. **AC-6:** No regression in existing tests.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A view that legitimately allows all roles (`required_roles = ()`) is flagged | Medium | Medium | Allow empty tuple but require a comment `# public` |
| A view that delegates to a per-method guard is flagged | Medium | Medium | Allow the comment `# delegated: see method` |
| Performance of the audit script on large codebases | Low | Low | Use `ast` parsing, not `import` |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Write `scripts/ci/audit_required_roles.py` | Backend | not-started |
| 2 | Enumerate every `TenantAPIView` and document the role matrix | Backend | not-started |
| 3 | Add `required_roles` to every view that is missing it | Backend | not-started |
| 4 | Add the `rbac-audit` CI job | DevOps | not-started |
| 5 | Update `docs/SECURITY_THREAT_MODEL.md` | Security Lead | not-started |
| 6 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/02_HIGH_PRIORITY/H-01_REVIEW_DECISION_RBAC](../../02_HIGH_PRIORITY/H-01_REVIEW_DECISION_RBAC/00_DISCOVERY.md) — first class to be fixed
- [upgrads/02_HIGH_PRIORITY/H-02_REVIEW_POLICY_RBAC](../../02_HIGH_PRIORITY/H-02_REVIEW_POLICY_RBAC/00_DISCOVERY.md) — second class to be fixed
- [backend/apps/reviews/api/views.py](../../../backend/apps/reviews/api/views.py) — reference implementation
- [docs/SECURITY_THREAT_MODEL.md](../../../docs/SECURITY_THREAT_MODEL.md) — A01 control
