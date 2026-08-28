# LEGAL-06: Implementation Guide

## Step 1: Model

### 1.1 `backend/apps/compliance/models.py`

```python
import hashlib

class LegalDocument(models.Model):
    document_type = models.CharField(max_length=64)
    version = models.CharField(max_length=16)
    content_en = models.TextField()
    content_ar = models.TextField()
    effective_date = models.DateField()
    supersedes_version = models.CharField(max_length=16, blank=True)
    published_by = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    content_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        unique_together = [("document_type", "version")]

    def save(self, *args, **kwargs):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content_en.encode("utf-8")).hexdigest()
        super().save(*args, **kwargs)
```

## Step 2: Data migration

Load the 7 documents from `docs/legal/`. A management command:

```python
# backend/apps/compliance/management/commands/load_legal_documents.py
from django.core.management.base import BaseCommand
from apps.compliance.models import LegalDocument
from apps.identity.models import User

class Command(BaseCommand):
    help = "Load the 7 legal documents from docs/legal/"

    def handle(self, *args, **opts):
        publisher = User.objects.filter(is_staff=True).first()
        # Loop through docs/legal/*/v1.0.md
        # Create LegalDocument rows
        # ...
```

## Step 3: Middleware

### 3.1 `backend/apps/compliance/middleware.py`

```python
from django.conf import settings
from django.http import JsonResponse
from apps.compliance.models import LegalDocument, LegalAcceptance
from django.utils import timezone


def current_documents():
    today = timezone.now().date()
    return {
        d.document_type: d
        for d in LegalDocument.objects.filter(effective_date__lte=today)
    }


class LegalAcceptanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "LEGAL_REACCEPTANCE_REQUIRED", True):
            return self.get_response(request)
        if not request.user.is_authenticated:
            return self.get_response(request)
        if not hasattr(request, "company") or not request.company:
            return self.get_response(request)
        current = current_documents()
        for doc_type, doc in current.items():
            accepted = LegalAcceptance.objects.filter(
                user=request.user, company=request.company, document_type=doc_type,
            ).order_by("-accepted_at").first()
            if not accepted or accepted.version != doc.version:
                return JsonResponse(
                    {"detail": "Re-acceptance required", "redirect": "/legal"},
                    status=403,
                )
        return self.get_response(request)
```

## Step 4: Tests

### 4.1 `backend/apps/compliance/tests/test_versioning.py`

```python
import pytest
from apps.compliance.models import LegalDocument, LegalAcceptance

pytestmark = pytest.mark.django_db


def test_reacceptance_required_on_new_version(make_user, make_company, force_login_company):
    owner = make_user(login_id="own")
    co = make_company(owner=owner, code="co")
    LegalDocument.objects.create(
        document_type="TERMS_OF_USE", version="1.0", content_en="...", content_ar="...",
        effective_date="2025-01-01", published_by=owner,
    )
    LegalDocument.objects.create(
        document_type="TERMS_OF_USE", version="1.1", content_en="...", content_ar="...",
        effective_date="2026-01-01", published_by=owner,
    )
    LegalAcceptance.objects.create(
        user=owner, company=co, document_type="TERMS_OF_USE", version="1.0", language="en",
    )
    client = force_login_company(owner, co)
    res = client.get("/api/v1/tenancy/companies/me/")
    assert res.status_code == 403
    # Accept the new version
    client.post(
        "/api/v1/compliance/legal-accept/",
        data={"document_type": "TERMS_OF_USE", "version": "1.1", "language": "en"},
        content_type="application/json",
    )
    res = client.get("/api/v1/tenancy/companies/me/")
    assert res.status_code == 200
```

## Step 5: Docs

1. Update `CHANGELOG.md` with a `LEGAL-06` entry.
2. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Model | `grep "class LegalDocument" backend/apps/compliance/models.py` | match |
| Middleware | `grep "LegalAcceptanceMiddleware" backend/config/settings/base.py` | match |
| Re-acceptance test | `pytest apps/compliance/tests/test_versioning.py` | passed |
| Content hash | `LegalDocument.objects.first().content_hash` | 64 chars |
