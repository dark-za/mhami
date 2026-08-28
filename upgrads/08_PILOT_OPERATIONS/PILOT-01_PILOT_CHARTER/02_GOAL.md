# PILOT-01: Goal and Plan

## SMART Goal

> Within **3 days**, draft the Charter template, implement the
> `PilotProgram` model, and wire the owner signature workflow (C-06).

## Acceptance Standards

### Standard 1: Charter template

`docs/pilot-evidence/01_CHARTER.md` covers:

- Company ID and Pilot Program ID (linked to `PilotProgram` DB record)
- Owner account ID
- Observation period (start/end UTC)
- Test environment (staging-equivalent)
- 3 branches target
- 30 employees target
- AI provider / Shadow Mode only
- Owner authorization (signed)

### Standard 2: Authorization Attestation

- Owner account ID
- Owner role
- Decision: authorize / decline / withdraw
- Date/time UTC
- Signature or approved electronic-record reference
- Conditions or exclusions

### Standard 3: Process

1. Pilot Manager writes the draft
2. Legal approves the scope
3. Security approves the test environment
4. Platform Owner signs
5. Charter enters the implementation space

### Standard 4: Model

```python
class PilotProgram(models.Model):
    company = models.ForeignKey("tenancy.Company", on_delete=models.PROTECT)
    owner_user = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    period_start = models.DateField()
    period_end = models.DateField()
    environment = models.CharField(max_length=64)  # staging, prod-shadow
    target_branches = models.IntegerField(default=3)
    target_employees = models.IntegerField(default=30)
    ai_provider = models.CharField(max_length=64, blank=True)
    ai_shadow_only = models.BooleanField(default=True)
    conditions = models.TextField(blank=True)
    status = models.CharField(max_length=16)  # draft, signed, active, closed
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey("identity.User", null=True, on_delete=models.PROTECT, related_name="signed_pilots")
    signature_audit_id = models.UUIDField(null=True)

    class Meta:
        unique_together = [("company", "owner_user", "period_start")]
```

---

## Implementation Plan

### Day 1 — Template

- [ ] Write `docs/pilot-evidence/01_CHARTER.md`.

### Day 2 — Model

- [ ] Add `PilotProgram` model.

### Day 3 — Signature

- [ ] Wire C-06 signature.
- [ ] Update `CHANGELOG.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | Template drafted |
| CP-2 | Model + migration |
| CP-3 | Signature wired |
| CP-4 | Docs |

---

## Cancellation Criteria

- A pilot without a signed Charter cannot enter "active" state.
