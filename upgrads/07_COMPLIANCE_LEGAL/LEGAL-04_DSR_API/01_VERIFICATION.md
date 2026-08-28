# LEGAL-04: Verification Commands

## Phase 1: Pre-Fix

```bash
Test-Path backend\apps\compliance\api\views.py
# Expected: missing or empty
```

## Phase 2: Post-Fix

```bash
# 1. DSRRequest model
Select-String -Path backend\apps\compliance\models.py -Pattern "class DSRRequest"
# Expected: 1 match

# 2. POST endpoint
curl -fsS -X POST http://localhost:8000/api/v1/compliance/dsr/ -H "Content-Type: application/json" -d '{"email":"x@example.com","request_type":"ACCESS"}'
# Expected: 201

# 3. GET endpoint (DPO)
curl -fsS -u dpo:$DPO_PASSWORD http://localhost:8000/api/v1/compliance/dsr/
# Expected: 200, list of requests

# 4. SLA reminder
Select-String -Path backend\apps -Pattern "DSR_SLA_DUE" -Recurse
# Expected: 1+ match

# 5. Tests
cd backend
pytest apps/compliance/tests/test_dsr.py -v
# Expected: ≥ 3 passed
```

## Phase 3: Regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```
