# PILOT-04: Usability Tests

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The pilot requires evidence that the core workflows can be completed by representative users. There is no usability protocol, participant script, task set, or findings register.

**Evidence gathered:**

```bash
Get-ChildItem docs\pilot-evidence -Filter "*usability*"
# Expected: no protocol
```

### Impact

| Dimension | Impact |
|---|---|
| Product | Friction remains invisible until production. |
| Compliance | No evidence of human oversight. |
| Pilot exit | Owner cannot assess usability objectively. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Protocol | missing | approved script |
| Representative participants | missing | 5 users across roles |
| Task completion data | missing | time, errors, success |
| Findings register | missing | prioritised evidence |

---

## 3. Goal Statement

> Within **5 days**, run five moderated usability sessions across the pilot roles, record task completion and observations, and publish an anonymised findings report.

### Acceptance Criteria

1. **AC-1:** Protocol covers login, task creation, review, and export.
2. **AC-2:** Five participants represent at least three roles.
3. **AC-3:** Consent and anonymisation are recorded.
4. **AC-4:** Findings include severity, evidence, owner, and disposition.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Participant data exposed | Low | High | Pseudonymous IDs, restricted evidence |
| Leading questions | Medium | Medium | Use neutral script and observer notes |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Draft protocol and consent | UX Lead | not-started |
| 2 | Recruit participants | Pilot Manager | not-started |
| 3 | Run sessions | UX Lead | not-started |
| 4 | Publish findings | UX Lead | not-started |
