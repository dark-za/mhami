# LEGAL-06: Goal and Plan

## SMART Goal

> Within **1 week**, add `LegalDocument` model, enforce `effective_date`,
> chain `supersedes_version`, and require re-acceptance on update.

## Acceptance Standards

### Standard 1: Model

```python
class LegalDocument(models.Model):
    document_type = models.CharField(max_length=64)  # TERMS_OF_USE, ...
    version = models.CharField(max_length=16)  # semver: 1.0.0
    content_en = models.TextField()
    content_ar = models.TextField()
    effective_date = models.DateField()
    supersedes_version = models.CharField(max_length=16, blank=True)
    published_by = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    content_hash = models.CharField(max_length=64)  # sha256 of content_en

    class Meta:
        unique_together = [("document_type", "version")]
```

### Standard 2: Middleware

`LegalAcceptanceMiddleware`:

1. On each request, find the current `LegalDocument` for each `document_type`.
2. Compare the user's most recent `LegalAcceptance` to the current `effective_date`.
3. If the user has accepted an older version, return 403 with `{detail: "Re-acceptance required", redirect: "/legal"}`.

### Standard 3: Re-acceptance

`POST /api/v1/compliance/legal-accept/` accepts a new version; `LegalAcceptance` row is created with the new `version`.

### Standard 4: Tests

| Test | Expected |
|---|---|
| `test_reacceptance_required_on_new_version` | 403 on state-changing calls |
| `test_middleware_allows_after_acceptance` | 200 |
| `test_supersedes_chain` | queryable |
| `test_content_hash` | stable |

---

## Implementation Plan

### Day 1-2 — Model

- [ ] Add `LegalDocument` model.
- [ ] Add data migration that loads the 7 documents from `docs/legal/`.

### Day 3 — Middleware

- [ ] Add `LegalAcceptanceMiddleware`.
- [ ] Wire into `MIDDLEWARE`.

### Day 4 — Frontend + tests

- [ ] Frontend banner.
- [ ] Tests.

### Day 5 — Docs

- [ ] Update `CHANGELOG.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | Model + data migration |
| CP-2 | Middleware |
| CP-3 | Re-acceptance flow |
| CP-4 | Tests |
| CP-5 | Docs |

---

## Cancellation Criteria

- If a user cannot re-accept (e.g. email loop) → allow DPO bypass with audit; do not silently skip.
