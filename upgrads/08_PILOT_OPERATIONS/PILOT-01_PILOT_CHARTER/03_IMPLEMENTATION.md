# PILOT-01: Implementation Guide

## Step 1: Charter template

### 1.1 `docs/pilot-evidence/01_CHARTER.md`

```markdown
# Pilot Charter

**Pilot Program ID:** <id>
**Company ID:** <id>
**Owner Account ID:** <id>
**Observation Period:** YYYY-MM-DD → YYYY-MM-DD (UTC)
**Test Environment:** staging-equivalent (no real customer data)

## 1. Scope

- **Branches:** 3 target
- **Employees:** 30 target
- **AI Provider:** <provider> (Shadow Mode only — no autonomous decision)
- **Out of scope:** Production traffic, real customer data, autonomous AI decisions, cross-tenant data

## 2. Authorization Attestation

I, <Owner name>, in my capacity as **Platform Owner**, hereby:

- [ ] **Authorize** the pilot as described above
- [ ] **Decline** the pilot
- [ ] **Withdraw** an existing authorization

**Decision:** _________________________
**Date / Time (UTC):** _________________________
**Signature / Electronic-record Reference:** _________________________
**Conditions or Exclusions:**

> <text>

---

## 3. Approval Trail

| Role | Name | Date |
|---|---|---|
| Pilot Manager | | |
| Legal | | |
| Security | | |
| Platform Owner | | |
```

## Step 2: Model

### 2.1 `backend/apps/pilot/models.py`

```python
class PilotProgram(models.Model):
    company = models.ForeignKey("tenancy.Company", on_delete=models.PROTECT)
    owner_user = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    period_start = models.DateField()
    period_end = models.DateField()
    environment = models.CharField(max_length=64)
    target_branches = models.IntegerField(default=3)
    target_employees = models.IntegerField(default=30)
    ai_provider = models.CharField(max_length=64, blank=True)
    ai_shadow_only = models.BooleanField(default=True)
    conditions = models.TextField(blank=True)
    status = models.CharField(max_length=16, default="draft")
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey(
        "identity.User", null=True, blank=True, on_delete=models.PROTECT, related_name="signed_pilots"
    )
    signature_audit_id = models.UUIDField(null=True, blank=True)

    class Meta:
        unique_together = [("company", "owner_user", "period_start")]
```

## Step 3: Wire C-06 signature

The `sign_pilot` view creates a signature audit row and links it to the `PilotProgram`:

```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sign_pilot(request, pk):
    pilot = PilotProgram.objects.get(pk=pk)
    if not request.user.is_staff:
        return Response({"detail": "Platform Owner only"}, status=403)
    decision = request.data["decision"]
    audit = write_audit_event(
        event="PILOT_CHARTER_SIGNED",
        actor=request.user,
        context={"pilot_id": str(pilot.id), "decision": decision, "conditions": request.data.get("conditions", "")},
    )
    pilot.status = "signed" if decision == "authorize" else "declined"
    pilot.signed_at = timezone.now()
    pilot.signed_by = request.user
    pilot.signature_audit_id = audit.id
    pilot.save()
    return Response({"id": str(pilot.id), "status": pilot.status})
```

## Step 4: Tests

```python
def test_pilot_charter_signs(make_user, make_company):
    owner = make_user(login_id="owner", is_staff=True)
    co = make_company(owner=owner, code="co")
    pilot = PilotProgram.objects.create(company=co, owner_user=owner, period_start="2030-01-01", period_end="2030-12-31", environment="staging")
    # POST /api/v1/pilot/programs/{id}/sign/
    # ... assert status == "signed", audit row written
```

## Step 5: Docs

1. Update `CHANGELOG.md` with a `PILOT-01` entry.
2. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Template | `Test-Path docs\pilot-evidence\01_CHARTER.md` | True |
| Model | `grep "class PilotProgram" backend/apps/pilot/models.py` | match |
| Signature | `grep "sign_pilot" backend/apps/pilot/api/views.py` | match |
