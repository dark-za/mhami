# LEGAL-03: Test Strategy

> **Rule:** every high-risk activity is in the DPIA; every mitigation is linked to an upgrade; the annual reminder fires.

## 1. Unit Tests

```bash
cd backend
pytest apps/compliance/tests/test_dpia.py -v
# Expected: ≥ 3 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/compliance/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Each activity has a mitigation upgrade

```bash
# A test loads the DPIA risks and asserts every row has a non-empty mitigation_upgrade OR
# owner with explicit "residual risk accepted" note.
cd backend
pytest apps/compliance/tests/test_dpia_mitigations.py -v
# Expected: passed
```

### 3.2 Annual reminder

```bash
cd backend
python manage.py shell -c "from apps.compliance.tasks import annual_dpia_review; annual_dpia_review()"
# Verify: a DPIA_REVIEW_DUE row is written
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| ≥ 4 activities in DPIA | passed |
| Each has 5 sections | passed |
| Each has mitigation upgrade | passed |
| Annual reminder | passed |

## 5. Cross-links

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-02_ROPA_REGISTER](..) — ROPA
- [upgrads/01_CRITICAL_FIXES/C-13_FACE_PRIVACY_ENFORCEMENT](../../01_CRITICAL_FIXES/C-13_FACE_PRIVACY_ENFORCEMENT/00_DISCOVERY.md)
- [upgrads/05_INFRASTRUCTURE/INFRA-03_BACKUP_S3_UPLOAD](../05_INFRASTRUCTURE/INFRA-03_BACKUP_S3_UPLOAD/00_DISCOVERY.md)
