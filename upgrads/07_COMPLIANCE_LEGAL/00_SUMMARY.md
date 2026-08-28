# Section 7: Regulatory Compliance (Compliance & Legal - PDPL)

## List of Fixes

| # | Title | Priority | Duration |
|---|---|---|---|
| LEGAL-01 | Draft legal documents | P0 | 4 weeks |
| LEGAL-02 | Record of Processing Activities (ROPA) | P0 | 1 week |
| LEGAL-03 | Data Protection Impact Assessment (DPIA) | P0 | 2 weeks |
| LEGAL-04 | Data Subject Rights API (DSR) | P0 | 1 week |
| LEGAL-05 | Data breach response plan | P0 | 1 week |
| LEGAL-06 | Document versioning | P0 | 1 week |

> Gate dependency: no real-user pilot, external AI transfer, connector
> enrollment with personal data, or production promotion may occur until the
> applicable Legal, Security, and Privacy approvals are recorded. Drafting
> documents is not itself evidence of PDPL readiness.

## LEGAL-01: Legal Documentation (Detail)

### Status
`docs/legal/README.md:3`:
> "**Placeholder only. These files must be drafted and reviewed by qualified legal counsel before use.**"

### Required documents
1. **Terms of Use**
2. **Privacy Notice**
3. **Data Processing Terms**
4. **AI Data Transfer Notice**
5. **Employee Privacy Acknowledgement**
6. **Retention and Deletion Policy**
7. **Support Access Authorization Terms**

### Structure
```
docs/legal/
├── README.md                    # ✅ Existing
├── 01_TERMS_OF_USE/
│   ├── v1.0.md                 # current
│   ├── v1.1.md                 # updated
│   └── CHANGELOG.md            # change log
├── 02_PRIVACY_NOTICE/
├── 03_DATA_PROCESSING_TERMS/
├── 04_AI_TRANSFER_NOTICE/
├── 05_EMPLOYEE_PRIVACY/
├── 06_RETENTION_DELETION/
├── 07_SUPPORT_ACCESS/
└── 08_TEMPLATES/               # templates
```

### Process
1. **Initial draft** by specialized legal counsel
2. **Review** by DPO (Data Protection Officer)
3. **Approval** by Platform Owner
4. **Publishing** in the UI as a readable document
5. **Acceptance tracking** in LegalAcceptance
6. **Annual review plan** or on major change

## LEGAL-02: ROPA (Record of Processing Activities) (Detail)

### Structure
```markdown
# ROPA - Record of Processing Activities

## Activity 1: Company Registration
- **Name:** Company Registration
- **Purpose:** Onboarding new tenants
- **Controller:** Platform (acting as processor for the tenant)
- **Recipient:** Mhami Operations
- **Data categories:** Company name, code, contact info, owner credentials
- **Data subject categories:** Business owners
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** Duration of contract + 90 days
- **Legal basis:** Contract performance, legitimate interest
- **Security measures:** Encryption at rest, TLS in transit, MFA

## Activity 2: Evidence Capture
... (per activity)
```

### ROPA API
```python
# apps/compliance/models.py
class ProcessingActivity(models.Model):
    name = models.CharField(max_length=200)
    purpose = models.TextField()
    legal_basis = models.CharField(max_length=200)
    data_categories = models.JSONField()
    recipients = models.JSONField()
    retention_days = models.IntegerField()
    cross_border = models.BooleanField(default=False)
    last_reviewed = models.DateField()

    class Meta:
        verbose_name = "ROPA Entry"
```

## LEGAL-03: DPIA (Detail)

### Sections
1. **Description** (nature, scope, context, purpose)
2. **Necessity assessment** (is the processing necessary)
3. **Risk assessment** (for each data subject right)
4. **Mitigation measures** (technical + organizational)
5. **Consultation** (DPO + stakeholders)

### Main Risks
- Face image capture → high-risk candidate until a trusted server-side detector,
  failure policy, retention, and false-negative evaluation are approved.
- AI analysis → external transfer is prohibited until purpose, legal basis,
  processor terms, destination, egress controls, and owner acceptance are approved.
- Hosting/cloud transfer → assess under the applicable Saudi PDPL requirements;
  do not assume SCC terminology or a foreign transfer mechanism is sufficient.
- Backups → remain high risk until encryption, remote retention, deletion, and a
  verified external restore drill are complete.

## LEGAL-04: DSR API (Detail)

### Rights
- **Right to Access**
- **Right to Rectification**
- **Right to Erasure**
- **Right to Restriction**
- **Right to Portability**
- **Right to Object**

### API
```python
# apps/compliance/api/views.py
class DSRRequestView(APIView):
    """Handle Data Subject Rights requests."""

    def post(self, request):
        serializer = DSRRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dsr = DSRRequest.objects.create(
            subject_email=request.data["email"],
            request_type=serializer.validated_data["request_type"],
            status="pending",
        )
        # Send email to DPO
        send_mail(...)
        # Schedule processing
        process_dsr_request.delay(str(dsr.id))
        return Response({"id": str(dsr.id), "status": "pending"}, status=201)
```

### Workflow
1. DSR request via web form
2. Email verification
3. DPO review
4. Identity verification
5. Action execution
6. Confirmation to subject

## LEGAL-05: Breach Response (Detail)

### Structure
```markdown
# Data breach response plan

## Definition
Data breach = any incident leading to:
- Unauthorized access to personal data
- Loss or alteration or disclosure of personal data
- Failure of confidentiality, integrity, or availability

## Severity levels
- **Critical (P0):** > 1000 data subjects
- **High (P1):** 100-1000
- **Medium (P2):** < 100

## Response
1. **0-1 hour:** Containment + notify CISO
2. **1-24 hours:** Investigation + impact assessment
3. **24-72 hours:** Notify SDAIA (if P0/P1)
4. **72 hours-7 days:** Notify data subjects
5. **7-30 days:** Root cause analysis + improvements

## Response team
- Incident Commander
- Security Lead
- DPO
- Legal Counsel
- Communications
- Platform Owner
```

## LEGAL-06: Versioning (Detail)

### Model
```python
class LegalDocument(models.Model):
    document_type = models.CharField(choices=LegalDocumentType.choices)
    version = models.CharField(max_length=16)  # semver: 1.0.0
    content_en = models.TextField()
    content_ar = models.TextField()
    effective_date = models.DateField()
    supersedes_version = models.CharField(max_length=16, blank=True)
    published_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        unique_together = [("document_type", "version")]
```

### Re-acceptance
- When a new `effective_date` arrives, the employee/owner can use the platform
- but `LegalAcceptance` must be for the current copy
- If old → request re-accept
