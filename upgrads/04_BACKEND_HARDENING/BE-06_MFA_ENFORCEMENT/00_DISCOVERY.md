# BE-06: Enforce MFA for Admin / Owner

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** MFA is **optional**. Platform Admins and tenant Owners can log in without a second factor. The middleware is in place but only fires when `MFA_ENFORCEMENT_ENABLED=True` (test setting). The default in `settings/base.py` is `False`. PDPL and Gate-B require mandatory MFA for high-privilege roles.

**Evidence gathered:**

```bash
# 1. Check the setting
Select-String -Path backend\config\settings -Pattern "MFA_ENFORCEMENT_ENABLED" -Recurse
# Expected: present, default False

# 2. Check the middleware
Test-Path backend\apps\identity\middleware.py
# Expected: True
Select-String -Path backend\apps\identity\middleware.py -Pattern "MFAEnforcementMiddleware"
# Expected: 1 match
```

### Impact

| Dimension | Impact |
|---|---|
| Security | A stolen password = full access. |
| Compliance | Gate-B (PDPL) requires MFA for Owner/Admin. |
| Operational | No way to roll out MFA gradually without breaking pilot. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `MFA_ENFORCEMENT_ENABLED` default | `False` | `True` in prod |
| `MFAEnforcementMiddleware` registered | yes | unchanged |
| Owner / Staff enrollment | optional | mandatory on first login |
| Recovery codes | optional | mandatory |
| Tests | 1 | ≥5 |

---

## 3. Goal Statement

> Within **1 week**, MFA is **mandatory** for `is_staff` users and tenant Owners. The middleware redirects unenrolled users to `/mfa/enroll`. The default for `MFA_ENFORCEMENT_ENABLED` is `True` in prod, `False` only in dev/test.

### Acceptance Criteria

1. **AC-1:** `MFA_ENFORCEMENT_ENABLED` is `True` in `config.settings.prod`, `False` in `dev` and `test`.
2. **AC-2:** `MFAEnforcementMiddleware` returns 403 on any state-changing request from an unenrolled Owner / Staff.
3. **AC-3:** The frontend redirects to `/mfa/enroll` on a 403 from MFA enforcement.
4. **AC-4:** After enrollment, the user can proceed.
5. **AC-5:** Recovery codes are generated and stored hashed.
6. **AC-6:** Tests cover: enrollment, login with MFA, login without MFA (rejected), recovery code, lockout.
7. **AC-7:** `compose.prod.yml` does NOT set `MFA_ENFORCEMENT_ENABLED=False`.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Pilot cannot log in because MFA is mandatory | High | High | Document the enrollment flow; provide recovery codes |
| Recovery code leak | Medium | High | Hash recovery codes; one-time use |
| Lockout | Medium | High | Allow admin reset (with audit row) |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Set `MFA_ENFORCEMENT_ENABLED=True` in prod settings | Backend | not-started |
| 2 | Confirm middleware is wired | Backend | not-started |
| 3 | Add tests | Backend | not-started |
| 4 | Frontend redirect | Frontend | not-started |
| 5 | Update `docs/SECURITY_AND_DATA_BASELINE.md` | Security Lead | not-started |
| 6 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/03_FRONTEND_REBUILD/FE-04_WORKFLOW_SCREENS](../../03_FRONTEND_REBUILD/FE-04_WORKFLOW_SCREENS/00_DISCOVERY.md) — enrollment UI
- [upgrads/02_HIGH_PRIORITY/H-01_REVIEW_DECISION_RBAC](../../02_HIGH_PRIORITY/H-01_REVIEW_DECISION_RBAC/00_DISCOVERY.md) — class-level guard pattern
- [docs/SECURITY_AND_DATA_BASELINE.md](../../../docs/SECURITY_AND_DATA_BASELINE.md)
