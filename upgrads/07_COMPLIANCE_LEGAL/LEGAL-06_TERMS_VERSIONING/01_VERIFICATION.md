# LEGAL-06: Verification Commands

## Phase 1: Pre-Fix

```bash
Select-String -Path backend\apps\compliance -Pattern "class LegalDocument" -Recurse
# Expected: 0
```

## Phase 2: Post-Fix

```bash
# 1. Model exists
Select-String -Path backend\apps\compliance\models.py -Pattern "class LegalDocument"
# Expected: 1 match

# 2. effective_date enforcement
cd backend
python manage.py shell -c "from apps.compliance.models import LegalDocument; print(LegalDocument.objects.filter(effective_date__lte='2030-01-01').count())"
# Expected: ≥ 1

# 3. Middleware check
Select-String -Path backend\apps\compliance\middleware.py -Pattern "LegalDocument|effective_date" -Recurse
# Expected: 1+ match

# 4. Re-acceptance test
pytest apps/compliance/tests/test_versioning.py -v
# Expected: passed
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
