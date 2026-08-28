# LEGAL-01: Implementation Guide

## Step 1: Document structure

### 1.1 Create folders

```bash
mkdir docs/legal/01_TERMS_OF_USE
mkdir docs/legal/02_PRIVACY_NOTICE
mkdir docs/legal/03_DATA_PROCESSING_TERMS
mkdir docs/legal/04_AI_TRANSFER_NOTICE
mkdir docs/legal/05_EMPLOYEE_PRIVACY
mkdir docs/legal/06_RETENTION_DELETION
mkdir docs/legal/07_SUPPORT_ACCESS
```

### 1.2 Template (per document)

```markdown
# <Document Title> v1.0

**Effective Date:** YYYY-MM-DD
**Supersedes:** (none)
**Language:** English (see v1.0.ar.md for Arabic)

## 1. Introduction

<counsel-drafted text>

## 2. Scope

<counsel-drafted text>

## 3. Definitions

<counsel-drafted text>

## ...sections...

## Counsel Approval

- **Counsel:** <name>, <bar number>
- **Date:** YYYY-MM-DD
- **Signature:** <hash or reference>
```

### 1.3 Place `v1.0.md` and `v1.0.ar.md` in each folder

> **Note:** the actual drafts are produced by counsel. This step captures the **structure** that the implementation will use; the draft text is delivered separately by counsel.

## Step 2: `LegalAcceptance` model

### 2.1 `backend/apps/compliance/models.py`

```python
class LegalAcceptance(models.Model):
    user = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    company = models.ForeignKey("tenancy.Company", on_delete=models.PROTECT)
    document_type = models.CharField(max_length=64)  # matches LegalDocumentType
    version = models.CharField(max_length=16)
    language = models.CharField(max_length=8)
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        unique_together = [("user", "company", "document_type", "version")]
```

## Step 3: Acceptance view

### 3.1 `backend/apps/compliance/api/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.compliance.models import LegalAcceptance, LegalDocument
from apps.audit.services import write_audit_event


class LegalAcceptanceView(APIView):
    def post(self, request):
        doc_type = request.data["document_type"]
        version = request.data["version"]
        language = request.data["language"]
        # Confirm the document exists and is published
        LegalDocument.objects.get_or_create(
            document_type=doc_type,
            version=version,
            defaults={"effective_date": "2030-01-01", "language": language},
        )
        acc = LegalAcceptance.objects.create(
            user=request.user,
            company=request.company,
            document_type=doc_type,
            version=version,
            language=language,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        write_audit_event(
            event="LEGAL_ACCEPTANCE",
            actor=request.user,
            company_id=str(request.company.id) if hasattr(request, "company") else None,
            context={
                "document_type": doc_type,
                "version": version,
                "language": language,
            },
        )
        return Response({"id": str(acc.id)}, status=status.HTTP_201_CREATED)
```

## Step 4: Re-acceptance

When `LegalDocument` is updated to a new version, the frontend must:

1. Detect that the user has accepted only an older version.
2. Show the new version.
3. Require acceptance before continuing.

The view already enforces uniqueness on `(user, company, document_type, version)`.

## Step 5: Tests

### 5.1 `backend/apps/compliance/tests/test_legal_acceptance.py`

```python
import pytest

from apps.compliance.models import LegalAcceptance
from apps.audit.models import AuditEvent

pytestmark = pytest.mark.django_db


def test_acceptance_creates_audit_row(make_user, make_company, force_login_company):
    owner = make_user(login_id="own")
    co = make_company(owner=owner, code="co")
    client = force_login_company(owner, co)
    res = client.post(
        "/api/v1/compliance/legal-accept/",
        data={"document_type": "TERMS_OF_USE", "version": "1.0", "language": "en"},
        content_type="application/json",
    )
    assert res.status_code == 201
    assert LegalAcceptance.objects.count() == 1
    assert AuditEvent.objects.filter(event="LEGAL_ACCEPTANCE").count() == 1


def test_acceptance_is_unique_per_version(make_user, make_company, force_login_company):
    owner = make_user(login_id="own-2")
    co = make_company(owner=owner, code="co-2")
    client = force_login_company(owner, co)
    for _ in range(2):
        client.post(
            "/api/v1/compliance/legal-accept/",
            data={"document_type": "TERMS_OF_USE", "version": "1.0", "language": "en"},
            content_type="application/json",
        )
    assert LegalAcceptance.objects.count() == 1


def test_reacceptance_on_new_version(make_user, make_company, force_login_company):
    owner = make_user(login_id="own-3")
    co = make_company(owner=owner, code="co-3")
    client = force_login_company(owner, co)
    client.post(
        "/api/v1/compliance/legal-accept/",
        data={"document_type": "TERMS_OF_USE", "version": "1.0", "language": "en"},
        content_type="application/json",
    )
    res = client.post(
        "/api/v1/compliance/legal-accept/",
        data={"document_type": "TERMS_OF_USE", "version": "1.1", "language": "en"},
        content_type="application/json",
    )
    assert res.status_code == 201
    assert LegalAcceptance.objects.filter(version="1.1").count() == 1
```

## Step 6: Docs

1. Update `docs/legal/README.md` with the document map.
2. Update `CHANGELOG.md` with a `LEGAL-01` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| 7 documents exist | `Get-ChildItem docs\legal -Recurse -Filter "v1.0.md"` | 7+ |
| Counsel sign-off | `Select-String docs\legal -Pattern "Counsel"` | ≥ 7 |
| Acceptance flow | `pytest apps/compliance/tests/test_legal_acceptance.py` | passed |
| Re-acceptance | `pytest apps/compliance/tests/test_legal_reacceptance.py` | passed |
| CHANGELOG | `grep "LEGAL-01" CHANGELOG.md` | match |
