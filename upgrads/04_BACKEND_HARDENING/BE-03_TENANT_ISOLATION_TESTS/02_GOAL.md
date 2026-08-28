# BE-03: Goal and Plan

## SMART Goal

> Within **1 week**, write a dedicated
> `backend/tests/test_tenant_isolation.py` with **≥50 tests** covering
> cross-tenant, cross-branch, role mismatch, and disabled membership
> for every endpoint that takes an external ID. All tests pass on
> `pytest -m permission`.

## Acceptance Standards

### Standard 1: Test matrix

For every endpoint in BE-02's list, ≥5 tests:

| # | Scenario | Expected |
|---|---|---|
| 1 | Happy path | 200/201 |
| 2 | Cross-tenant reference | 403/404 |
| 3 | Cross-branch reference (when branch-scoped) | 403/404 |
| 4 | Role mismatch | 403 |
| 5 | Disabled membership | 403 |

### Standard 2: Marker

All tests carry `@pytest.mark.permission`.

### Standard 3: Performance

`pytest -m permission` runs in < 60s.

### Standard 4: Documentation

`docs/TEST_STRATEGY.md` lists `test_tenant_isolation.py` under the **Permission** layer.

---

## Implementation Plan

### Day 1-2 — Inventory

- [ ] Enumerate endpoints (see BE-02 list).
- [ ] Identify the role matrix per endpoint.

### Day 3-5 — Tests

- [ ] Write 5 tests per endpoint.
- [ ] Use the `make_*` factories.
- [ ] Mark with `@pytest.mark.permission`.

### Day 5 — CI

- [ ] Run `pytest -m permission` in CI.
- [ ] Update `docs/TEST_STRATEGY.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | Inventory done |
| CP-2 | ≥50 tests pass |
| CP-3 | `pytest -m permission` < 60s |
| CP-4 | Docs updated |

---

## Cancellation Criteria

- If tests run too slow → mark slow ones with `@pytest.mark.slow`; do not skip.
