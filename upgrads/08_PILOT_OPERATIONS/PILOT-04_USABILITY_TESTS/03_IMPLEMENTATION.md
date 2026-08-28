# PILOT-04: Implementation Guide

## Step 1: Protocol

Create `docs/pilot-evidence/04_USABILITY_PROTOCOL.md` with:

```markdown
# Usability Test Protocol

## Consent
The session is voluntary. Notes are anonymised. The participant may stop at any time.

## Moderator Script
1. Ask the participant to think aloud.
2. Do not coach or correct.
3. Record time, errors, and completion state.
4. Ask confidence (1-5) after each task.

## Session Tasks
- Sign in and select the pilot company.
- Create and assign a task.
- Review evidence.
- Export a weekly report.
- Accept or reject an AI suggestion in Shadow Mode.

## Session Record
| Participant ID | Role | Date | Moderator |
|---|---|---|---|
| | | | |

| Task | Outcome | Seconds | Critical Error | Confidence |
|---|---|---:|---|---:|
| | | | | |
```

## Step 2: Findings

Create `docs/pilot-evidence/04_USABILITY_FINDINGS.md` and replace participant identifiers with `P-01` through `P-05`.

```markdown
# Usability Findings

| ID | Task | Observation | Severity | Evidence | Owner | Disposition |
|---|---|---|---|---|---|---|
| U-001 | | | blocker/major/minor | | | |
```

## Step 3: Evidence handling

- Store raw notes in the restricted pilot evidence location.
- Publish only anonymised aggregates.
- Retain consent records according to the data retention policy.

## Step 4: Review

- UX Lead checks analysis.
- Security checks data minimisation.
- Pilot Manager records each finding's disposition.

## Step 5: Tests

```bash
# Evidence completeness
Select-String -Path docs\pilot-evidence\04_USABILITY_FINDINGS.md -Pattern "U-001|Severity|Disposition"
```
