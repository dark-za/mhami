# BE-06: Goal and Plan

## SMART Goal

> Within **1 week**, MFA is **mandatory** for `is_staff` users and
> tenant Owners. The middleware returns 403 on state-changing requests
> from unenrolled users, and the frontend redirects to `/mfa/enroll`.

## Acceptance Standards

### Standard 1: Settings

| Settings file | MFA_ENFORCEMENT_ENABLED |
|---|---|
| `config.settings.prod` | `True` |
| `config.settings.dev` | `False` |
| `config.settings.test` | `True` (to exercise the path) |
| `compose.prod.yml` | (no override; let prod setting win) |

### Standard 2: Middleware

```python
# apps/identity/middleware.py
class MFAEnforcementMiddleware:
    def __call__(self, request):
        if not settings.MFA_ENFORCEMENT_ENABLED:
            return self.get_response(request)
        if not request.user.is_authenticated:
            return self.get_response(request)
        if not is_state_changing(request):
            return self.get_response(request)
        if not (request.user.is_staff or has_owner_role(request.user, request.session.get("company_id"))):
            return self.get_response(request)
        if not has_verified_mfa(request.user):
            return JsonResponse({"detail": "MFA enrollment required", "redirect": "/mfa/enroll"}, status=403)
        return self.get_response(request)
```

### Standard 3: Tests

| Test | Expected |
|---|---|
| `test_enrolled_user_can_post` | 200 |
| `test_unenrolled_owner_cannot_post` | 403 |
| `test_unenrolled_owner_can_get` | 200 |
| `test_unenrolled_employee_can_post` | 200 (not in scope) |
| `test_recovery_code_works` | 200 |
| `test_locked_out_after_5_attempts` | 429 / lockout |

### Standard 4: Frontend redirect

On a 403 with `detail: "MFA enrollment required"`, the frontend redirects to `/mfa/enroll`.

---

## Implementation Plan

### Day 1 — Settings

- [ ] Set prod default `True`.
- [ ] Confirm dev/test defaults.

### Day 2 — Middleware

- [ ] Confirm wired in `MIDDLEWARE`.

### Day 3-4 — Tests

- [ ] Add 5+ tests.
- [ ] Frontend redirect logic.

### Day 5 — Docs

- [ ] Update `docs/SECURITY_AND_DATA_BASELINE.md`.
- [ ] Update `CHANGELOG.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | Prod default True |
| CP-2 | Middleware wired |
| CP-3 | Tests pass |
| CP-4 | Frontend redirects |
| CP-5 | Docs updated |

---

## Cancellation Criteria

- If MFA enrollment UX is not ready → keep the prod default `False` until FE-04 ships; document the gap.
