# C-05: Create Real Pilot Evidence (Replace UNFILLED Templates)

## 1. Discovery Summary

### Current State

**Problem:** All files `docs/pilot-evidence/01..08` contain the phrase "**UNFILLED TEMPLATE - NOT EVIDENCE**". There is no real pilot.

**Guide:**

`docs/pilot-evidence/01_PILOT_CHARTER_AND_OWNER_AUTHORIZATION.md:3`:
```
> **UNFILLED TEMPLATE - NOT EVIDENCE.** This document becomes evidence only when the required system records and authorization evidence links are completed by authorized humans.
```

`docs/pilot-evidence/04_DAILY_OPERATIONAL_LOG.md:3`:
```
> **UNFILLED TEMPLATE - NOT EVIDENCE.** Enter observed events only, with source links.
```

Same phrase in `02, 03, 05, 06, 07, 08`.

### Impact

| Dimension | Impact |
|---|---|
| Compliance | PHASE12 exit not possible without pilot evidence |
| Directories | No operational evidence exists |
| Owner decision | Cannot make a decision without evidence |
| Phase 13 | Cannot be started |

---

## 2. Gap

| Document | Current | Target |
|---|---|---|
| 01 Pilot Charter | UNFILLED | Filled + signed |
| 02 Branch Roster | UNFILLED | Filled with real names |
| 03 Legal Acceptance | UNFILLED | Links to logs |
| 04 Daily Log | UNFILLED | Real daily events |
| 05 Weekly Metrics | UNFILLED | Measurements from the system |
| 06 Resilience Tests | UNFILLED | Test results |
| 07 Issue/Change Register | UNFILLED | Problems and decisions |
| 08 Handoff Checklist | UNFILLED | Verified list |

---

## 3. Goal

> Within **2 weeks**, run a real pilot with 3 branches and 30 employees and collect real evidence.

### Acceptance Standards

1. AC-1: 3 real PilotWeeklyReport entries recorded in the system.
2. AC-2: 14 days of Daily Log filled in.
3. AC-3: Pilot Charter signed by the Platform Owner.
4. AC-4: Legal Acceptance links for four types of documents.
5. AC-5: No UNFILLED in any file.

---

## 4. Sub-tasks

- [ ] Recruit Pilot Company (Internal)
- [ ] Record 3 branches + 30 employees
- [ ] Sign Legal Acceptance (terms, privacy, ai_transfer, employee_privacy)
- [ ] Run pilot for 2 weeks
- [ ] Create PilotWeeklyReport each week
- [ ] Fill Daily Log daily
- [ ] Sign Owner on Charter
- [ ] Update all files by removing UNFILLED

---

## 5. Implementation Plan

### Week 1: Preparation

**Day 1-2:**
- [ ] Identify Pilot Company (Internal)
- [ ] Choose 3 branches and 30 employees
- [ ] Distribute Chrome devices

**Day 3-4:**
- [ ] Complete Branch Roster
- [ ] Complete Legal Acceptance
- [ ] Complete Pilot Charter
- [ ] Owner signature

**Day 5:**
- [ ] Train employees
- [ ] Test capture flow
- [ ] Begin Staging run

### Week 2: Run

**Daily:**
- [ ] Daily Log
- [ ] Monitor errors
- [ ] Issue tracking

**Last day:**
- [ ] Weekly metrics snapshot

### Week 3: Documentation

- [ ] PilotWeeklyReport #1, #2
- [ ] Issue Register
- [ ] Resilience Tests
- [ ] Handoff Checklist
- [ ] Owner final decision
