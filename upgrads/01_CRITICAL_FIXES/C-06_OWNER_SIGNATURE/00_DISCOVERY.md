# C-06: Create Platform Owner Signature Workflow (Owner Signature Workflow)

## 1. Discovery Summary

### Current State

**Problem:** `PHASE12_EXIT_DOSSIER.md` contains an empty signature field:
```
Approver: ____________________  Date: ____________________  Role: Platform Owner
```

There is no workflow to record the signature digitally, and no link to the Audit log.

**Guide:**

`docs/PHASE12_EXIT_DOSSIER.md:60-64`:
```markdown
### Owner Signature / Approval

- [ ] Approved — proceed to handoff to `LAUNCH-GATE-03`
- [ ] Owner-approved release decision recorded for the carried items
- [ ] Not approved — return to pilot operations with specific findings

Approver: ____________________  Date: ____________________  Role: Platform Owner
```

### Impact

- Cannot verify the Owner's approval
- Decisions are not recorded in Audit
- Cannot transition to Phase 13
- No traceability for decisions

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Signature workflow | none | digital workflow |
| Audit event | No | `EXIT_DECISION_SIGNED` |
| Linking decision to documentation | Manual | Logical reference |
| Revocation | not possible | possible with `EXIT_DECISION_REVOKED` |
| Verification | Visual | HMAC encrypted |

---

## 3. Goal

> Create `ExitDecision` model + API + UI + Audit integration.

### Acceptance Standards

1. AC-1: Platform Owner can sign from the UI.
2. AC-2: The signature is recorded in `AuditEvent` with HMAC.
3. AC-3: The signature carries a timestamp + rationale.
4. AC-4: The signature can be revoked before lock.
5. AC-5: PHASE12_EXIT_DOSSIER.md is updated with a link to the decision.

---

## 4. Implementation

### 4.1 New Model

**File:** `backend/apps/platform_core/models.py` (Add)

```python
class ExitDecision(models.Model):
    """Records a platform-owner's binding decision on a phase exit dossier.

    Decisions are immutable once signed. Revocations create a new decision
    that supersedes the previous one. Each decision is captured in the
    audit chain for traceability.
    """

    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        CONDITIONAL = "conditional", "Conditional approval"
        REJECTED = "rejected", "Rejected"
        DEFERRED = "deferred", "Deferred"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase = models.CharField(max_length=16)  # e.g. "phase_12"
    decision = models.CharField(max_length=16, choices=Decision.choices)
    rationale = models.TextField()
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    signed_at = models.DateTimeField(auto_now_add=True)
    supersedes = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="superseded_by",
    )
    signature_hmac = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["phase", "signed_at"]),
            models.Index(fields=["phase", "decision"]),
        ]
```

### 4.2 API

**File:** `backend/apps/platform_core/api/views.py` (Add)

```python
class ExitDecisionView(TenantAPIView):
    """Sign a phase exit decision. Restricted to Platform Administrator."""

    @extend_schema(request=ExitDecisionCreateSerializer, responses=ExitDecisionSerializer)
    def post(self, request, phase: str):
        if not request.user.is_staff:
            raise PlatformAPIException("Only platform administrators can sign exit decisions.")

        serializer = ExitDecisionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        decision = ExitDecision.objects.create(
            phase=phase,
            decision=serializer.validated_data["decision"],
            rationale=serializer.validated_data["rationale"],
            signed_by=request.user,
            metadata=serializer.validated_data.get("metadata", {}),
        )

        # Sign with HMAC
        decision.signature_hmac = _sign_decision(decision)
        decision.save(update_fields=["signature_hmac"])

        # Audit
        record_audit_event(
            event_type="EXIT_DECISION_SIGNED",
            target_type="exit_decision",
            target_id=str(decision.id),
            actor_id=str(request.user.id),
            metadata={
                "phase": phase,
                "decision": decision.decision,
                "rationale": decision.rationale[:200],
            },
        )
        return Response(ExitDecisionSerializer(decision).data, status=201)
```

### 4.3 Frontend UI

**File:** `frontend/src/pages/ExitDecisionPage.tsx`

```typescript
export function ExitDecisionPage() {
  const [decision, setDecision] = useState<'approved'|'rejected'|'conditional'>('approved');
  const [rationale, setRationale] = useState('');

  const handleSubmit = async () => {
    await api(`/api/v1/platform/exit-decisions/phase_12`, {
      method: 'POST',
      body: { decision, rationale },
    });
  };

  return (
    <div>
      <h1>Phase 12 Exit Decision</h1>
      <select value={decision} onChange={e => setDecision(e.target.value as any)}>
        <option value="approved">Approved</option>
        <option value="conditional">Conditional</option>
        <option value="rejected">Rejected</option>
        <option value="deferred">Deferred</option>
      </select>
      <textarea value={rationale} onChange={e => setRationale(e.target.value)} />
      <button onClick={handleSubmit}>Sign Decision</button>
    </div>
  );
}
```
