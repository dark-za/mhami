# BE-05: Log Failed Login Attempts

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** A user typing a wrong password or hitting a non-existent company gets no audit row. The platform cannot detect brute-force or credential-stuffing because the `LOGIN_FAILED` event is missing.

**Evidence gathered:**

```bash
Select-String -Path backend\apps\tenancy\auth_backends.py -Pattern "LOGIN_FAILED|record_login_failure"
# Expected today: 0 matches (no record_login_failure call)
```

### Impact

| Dimension | Impact |
|---|---|
| Security | No detection of brute-force. |
| Compliance | PDPL requires an audit of authentication events. |
| Operational | On-call has no signal for a spike in failed logins. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `record_login_failure` helper | missing | yes |
| Auth backend calls it on every failure | no | yes |
| `LOGIN_FAILED` audit event | missing | yes |
| Brute-force metric in INFRA-04 | missing | yes |

---

## 3. Goal Statement

> Within **1 day**, add `record_login_failure(request, login_id, reason, company_id=None)` and call it on every authentication failure path. The `LoginFailuresHigh` alert from INFRA-04 is wired.

### Acceptance Criteria

1. **AC-1:** `apps/tenancy/services.py` (or `auth_backends.py`) exposes `record_login_failure`.
2. **AC-2:** The auth backend calls it on: company not found, invalid credentials, company unavailable, locked account, MFA required.
3. **AC-3:** The audit row has `event="LOGIN_FAILED"` and context `{login_id_hash, company_code_hash, reason, ip, ua}` (no plaintext password).
4. **AC-4:** A test asserts each failure path writes a row.
5. **AC-5:** The INFRA-04 `LoginFailuresHigh` alert is wired.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Logging the plaintext password | Medium | High | Hash `login_id` with SHA-256; never log password |
| Performance regression | Low | Low | The audit row is async via the existing chain |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `record_login_failure` helper | Backend | not-started |
| 2 | Wire into auth backend | Backend | not-started |
| 3 | Add tests | Backend | not-started |
| 4 | Confirm `LoginFailuresHigh` alert | DevOps | not-started |
| 5 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/04_BACKEND_HARDENING/BE-04_AUDIT_INTEGRITY](..) — chain
- [upgrads/05_INFRASTRUCTURE/INFRA-04_PROMETHEUS_GRAFANA](../05_INFRASTRUCTURE/INFRA-04_PROMETHEUS_GRAFANA/00_DISCOVERY.md) — alert
