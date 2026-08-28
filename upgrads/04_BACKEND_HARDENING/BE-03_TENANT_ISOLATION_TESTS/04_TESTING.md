# BE-03: Test Strategy

> **Rule:** every endpoint in BE-02's list has ≥5 tests in `test_tenant_isolation.py`.

## 1. Unit Tests

Not applicable.

## 2. Integration Tests

### 2.1 Collect

```bash
cd backend
pytest -m permission --collect-only -q | Select-Object -Last 2
# Expected: ≥ 50
```

### 2.2 Run

```bash
cd backend
pytest -m permission
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### 2.3 Performance

```bash
cd backend
time pytest -m permission
# Expected: < 60s
```

---

## 3. End-to-End Tests

### 3.1 `pytest -m "not slow"` — no regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```

### 3.2 Docs

```bash
Select-String -Path docs\TEST_STRATEGY.md -Pattern "test_tenant_isolation"
# Expected: 1+ match
```

---

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| `pytest -m permission` | ≥ 50 | passed |
| `pytest -m "not slow"` | N | green |
| Docs | 1 | updated |

---

## 5. Run Tests

### 5.1 Local

```bash
cd backend
pytest -m permission -v
```

### 5.2 CI

The `backend` job runs `pytest -m permission` in addition to the default run.

### 5.3 Failure simulation

| Scenario | Expected |
|---|---|
| Revert the test file | count drops below 50 |
| Add a test that does not use the factories | pytest still passes, but is brittle |

---

## 6. Cross-links

- [upgrads/04_BACKEND_HARDENING/BE-01_RBAC_AUDIT](..)
- [upgrads/04_BACKEND_HARDENING/BE-02_SERIALIZER_VALIDATION](..)
- [upgrads/06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS](../06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS/00_DISCOVERY.md)
