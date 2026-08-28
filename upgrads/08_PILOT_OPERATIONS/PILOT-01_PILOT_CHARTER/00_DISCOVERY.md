# PILOT-01: Draft Authentic Pilot Charter

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** A pilot must be authorised by a binding **owner decision** that links a specific tenant, owner account, observation period, environment, scope, and conditions. The current repository has placeholder text and no `PilotProgram` model that ties the charter to the rest of the platform.

**Evidence gathered:**

```bash
Test-Path docs\pilot-evidence\charter.md
# Expected: placeholder

Select-String -Path backend\apps -Pattern "PilotProgram" -Recurse
# Expected: 0 or partial
```

### Impact

| Dimension | Impact |
|---|---|
| Compliance | Gate-E requires a binding owner decision. |
| Operational | No audit trail from charter → exit decision. |
| Legal | No record of what was authorised. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Charter template | missing | yes |
| `PilotProgram` model | missing | yes |
| Owner authorisation (signature) | missing | yes |
| Conditions / exclusions | missing | yes |

---

## 3. Goal Statement

> Within **3 days**, draft the Charter template, implement the `PilotProgram` model, and wire the owner signature workflow (C-06).

### Acceptance Criteria

1. **AC-1:** `docs/pilot-evidence/01_CHARTER.md` template exists.
2. **AC-2:** `apps/pilot/models.py::PilotProgram` exists with: company, owner_user, period, environment, scope, conditions, status.
3. **AC-3:** The Charter's `Owner Authorization` section is signed via C-06.
4. **AC-4:** The signed Charter is the source of truth for what the pilot is and is not.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Charter is signed by a non-owner | Medium | High | C-06 requires Platform Owner role |
| Charter is reused across tenants | Medium | High | Unique constraint on `(company, owner, period)` |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Write Charter template | Pilot Manager | not-started |
| 2 | Add `PilotProgram` model | Backend | not-started |
| 3 | Wire C-06 signature | Backend | not-started |
| 4 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/01_CRITICAL_FIXES/C-06_OWNER_SIGNATURE](../../01_CRITICAL_FIXES/C-06_OWNER_SIGNATURE/00_DISCOVERY.md)
- [upgrads/08_PILOT_OPERATIONS/PILOT-06_OWNER_DECISION](..) — exit decision
- [docs/pilot-evidence/01_CHARTER.md](../../../docs/pilot-evidence/01_CHARTER.md) (target)
