# PILOT-06: Implementation Guide

## Step 1: Decision template

Create `docs/pilot-evidence/06_OWNER_DECISION.md`:

```markdown
# Pilot Owner Decision

**Pilot ID:**
**Evidence Manifest Hash:**
**Review Date (UTC):**

## Gate Checklist

| Gate | Evidence Reference | Status | Reviewer |
|---|---|---|---|
| Charter | | pass/fail | |
| Daily logs | | pass/fail | |
| Weekly reports | | pass/fail | |
| Usability | | pass/fail | |
| Capacity | | pass/fail | |
| Security / privacy | | pass/fail | |

## Decision

- [ ] Expand
- [ ] Continue
- [ ] Remediate
- [ ] Stop

**Rationale:**

**Conditions:**

| Action | Owner | Due (UTC) | Status |
|---|---|---|---|
| | | | |

## Authorization

**Platform Owner Account:**
**Signature / Electronic-record Reference:**
**Signed At (UTC):**
```

## Step 2: Backend decision enforcement

```python
VALID_DECISIONS = {"expand", "continue", "remediate", "stop"}


def record_owner_decision(pilot, actor, decision, manifest_hash, rationale, conditions):
    if not actor.is_staff:
        raise PermissionDenied("Platform Owner only")
    if decision not in VALID_DECISIONS:
        raise ValidationError("Invalid decision")
    if not manifest_hash:
        raise ValidationError("Evidence manifest is required")
    event = write_audit_event(
        event="PILOT_OWNER_DECISION",
        actor=actor,
        context={"pilot_id": str(pilot.id), "decision": decision, "manifest_hash": manifest_hash, "rationale": rationale, "conditions": conditions},
    )
    pilot.status = "closed" if decision == "stop" else decision
    pilot.signature_audit_id = event.id
    pilot.save(update_fields=["status", "signature_audit_id"])
    return event
```

## Step 3: Closure

For `stop`:

1. Disable pilot activation.
2. Notify stakeholders.
3. Export required evidence.
4. Apply retention schedule.
5. Record closure completion.

## Step 4: Tests

```python
def test_owner_stop_requires_manifest(owner, pilot):
    with pytest.raises(ValidationError):
        record_owner_decision(pilot, owner, "stop", "", "reason", [])
```
