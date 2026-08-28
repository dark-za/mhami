# PILOT-06: Owner Decision

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** Pilot evidence must culminate in a recorded owner decision: expand, continue, remediate, or stop. The repository has no decision template, gate checklist, or link from pilot evidence to an immutable owner record.

**Evidence gathered:**

```bash
Select-String -Path docs backend -Pattern "Owner Decision|Go.No-Go|PILOT_EXIT" -Recurse
# Expected: 0 or partial
```

### Impact

| Dimension | Impact |
|---|---|
| Governance | No accountable go/no-go decision. |
| Legal | No record of conditions and dissent. |
| Operations | Pilot may continue without an explicit mandate. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Decision template | missing | approved |
| Gate checklist | missing | complete |
| Evidence references | scattered | linked manifest |
| Owner signature | missing | immutable audit record |

---

## 3. Goal Statement

> Within **2 days** of pilot evidence completion, compile the gate checklist, link all evidence, and record a signed owner decision with conditions and follow-up actions.

### Acceptance Criteria

1. **AC-1:** Decision template has expand / continue / remediate / stop options.
2. **AC-2:** Charter, weekly reports, usability, capacity, and security evidence are linked.
3. **AC-3:** Platform Owner signature is recorded with UTC timestamp.
4. **AC-4:** A stop decision disables pilot activation and triggers retention/closure actions.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Decision made with incomplete evidence | Medium | High | Checklist blocks submission |
| Conditions not tracked | Medium | High | Mandatory conditions and action owners |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Draft gate checklist | Pilot Manager | not-started |
| 2 | Link evidence manifest | Pilot Manager | not-started |
| 3 | Implement signed decision | Backend | not-started |
| 4 | Record closure actions | Operations | not-started |

---

## 6. References

- [upgrads/08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER](..)
- [upgrads/08_PILOT_OPERATIONS/PILOT-03_WEEKLY_REPORT](..)
- [upgrads/08_PILOT_OPERATIONS/PILOT-04_USABILITY_TESTS](..)
- [upgrads/08_PILOT_OPERATIONS/PILOT-05_CAPACITY_MEASUREMENT](..)
