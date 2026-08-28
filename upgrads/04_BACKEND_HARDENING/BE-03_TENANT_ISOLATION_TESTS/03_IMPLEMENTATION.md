# BE-03: Implementation Guide

## Step 1: Inventory

The endpoints to test (from BE-02):

| Endpoint | URL | Field | Model |
|---|---|---|---|
| `MyView` (tasks) | `POST /api/v1/tasks/instances/` | `branch_id`, `user_id`, `template_id` | Branch, User, TaskTemplate |
| `EvidenceView` | `POST /api/v1/evidence/items/` | `capture_id`, `task_id` | CaptureSession, TaskInstance |
| `ReviewDecisionView` | `POST /api/v1/reviews/decisions/{id}/decide/` | `decision_id` | ReviewDecision |
| `ExportRequestView` | `POST /api/v1/exports/requests/` | `company_id` | Company (foreign rejected) |
| `BackupRestoreView` | `POST /api/v1/backups/restore/` | `backup_id` | BackupRun |

## Step 2: Test file

### 2.1 New file: `backend/tests/test_tenant_isolation.py`

```python
"""Tenant isolation test suite.

Every endpoint that takes an external ID is tested for:
- happy path
- cross-tenant reference
- cross-branch reference
- role mismatch
- disabled membership
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.permission]


# --- tasks ---


def test_tasks_happy(make_user, make_company, make_branch, force_login_company, make_task_template):
    owner = make_user(login_id="own-1")
    co = make_company(owner=owner, code="co-1")
    b = make_branch(company=co, code="b-1")
    client = force_login_company(owner, co)
    res = client.get("/api/v1/tasks/instances/")
    assert res.status_code == 200


def test_tasks_cross_tenant(make_user, make_company, force_login_company):
    a = make_user(login_id="a")
    b = make_user(login_id="b")
    co_a = make_company(owner=a, code="co-a")
    co_b = make_company(owner=b, code="co-b")
    client = force_login_company(a, co_a)
    res = client.get(f"/api/v1/tasks/?company_id={co_b.id}")
    assert res.status_code in (403, 404)


def test_tasks_cross_branch(make_user, make_company, make_branch, force_login_company, make_membership):
    owner = make_user(login_id="sup")
    co = make_company(owner=owner, code="co")
    b1 = make_branch(company=co, code="b-1")
    make_branch(company=co, code="b-2")
    make_membership(user=owner, company=co, role="supervisor", branch=b1)
    client = force_login_company(owner, co)
    res = client.get(f"/api/v1/tasks/?branch={b1.id}")
    assert res.status_code == 200


def test_tasks_role_mismatch(make_user, make_company, force_login_company):
    employee = make_user(login_id="emp-1")
    co = make_company(code="co")
    make_company(owner=make_user(login_id="other"), code="co-2")
    client = force_login_company(employee, co)
    res = client.post("/api/v1/tasks/run/", data={}, content_type="application/json")
    assert res.status_code == 403


def test_tasks_disabled_membership(make_user, make_company, make_membership, force_login_company):
    u = make_user(login_id="dis-1")
    co = make_company(code="co")
    make_membership(user=u, company=co, role="owner", active=False)
    client = force_login_company(u, co)
    res = client.get("/api/v1/tasks/instances/")
    assert res.status_code in (401, 403)


# --- evidence ---


def test_evidence_happy(make_user, make_company, force_login_company):
    owner = make_user(login_id="own")
    co = make_company(owner=owner, code="co")
    client = force_login_company(owner, co)
    res = client.get("/api/v1/evidence/items/")
    assert res.status_code == 200


def test_evidence_cross_tenant(make_user, make_company, force_login_company):
    a = make_user(login_id="a")
    b = make_user(login_id="b")
    co_a = make_company(owner=a, code="co-a")
    co_b = make_company(owner=b, code="co-b")
    client = force_login_company(a, co_a)
    res = client.get(f"/api/v1/evidence/items/?company_id={co_b.id}")
    assert res.status_code in (403, 404)


def test_evidence_cross_branch(make_user, make_company, make_branch, make_membership, force_login_company):
    owner = make_user(login_id="own-2")
    co = make_company(owner=owner, code="co")
    make_branch(company=co, code="b-1")
    b2 = make_branch(company=co, code="b-2")
    make_membership(user=owner, company=co, role="supervisor", branch=b2)
    client = force_login_company(owner, co)
    res = client.get(f"/api/v1/evidence/items/?branch=other-branch")
    assert res.status_code in (403, 404)


def test_evidence_role_mismatch(make_user, make_company, force_login_company):
    employee = make_user(login_id="emp-2")
    co = make_company(code="co")
    client = force_login_company(employee, co)
    res = client.delete(f"/api/v1/evidence/items/00000000-0000-0000-0000-000000000000/")
    assert res.status_code in (403, 404)


def test_evidence_disabled(make_user, make_company, make_membership, force_login_company):
    u = make_user(login_id="dis-2")
    co = make_company(code="co")
    make_membership(user=u, company=co, role="owner", active=False)
    client = force_login_company(u, co)
    res = client.get("/api/v1/evidence/items/")
    assert res.status_code in (401, 403)


# --- reviews ---


def test_reviews_happy(make_user, make_company, force_login_company):
    owner = make_user(login_id="own-3")
    co = make_company(owner=owner, code="co")
    client = force_login_company(owner, co)
    res = client.get("/api/v1/reviews/decisions/")
    assert res.status_code == 200


def test_reviews_cross_tenant(make_user, make_company, force_login_company):
    a = make_user(login_id="a-3")
    b = make_user(login_id="b-3")
    co_a = make_company(owner=a, code="co-a-3")
    co_b = make_company(owner=b, code="co-b-3")
    client = force_login_company(a, co_a)
    res = client.get(f"/api/v1/reviews/decisions/?company_id={co_b.id}")
    assert res.status_code in (403, 404)


def test_reviews_cross_branch(make_user, make_company, make_branch, make_membership, force_login_company):
    owner = make_user(login_id="own-4")
    co = make_company(owner=owner, code="co")
    b1 = make_branch(company=co, code="b-1")
    b2 = make_branch(company=co, code="b-2")
    make_membership(user=owner, company=co, role="supervisor", branch=b1)
    client = force_login_company(owner, co)
    res = client.get(f"/api/v1/reviews/decisions/?branch={b2.id}")
    assert res.status_code in (403, 404)


def test_reviews_role_mismatch(make_user, make_company, force_login_company):
    employee = make_user(login_id="emp-3")
    co = make_company(code="co")
    client = force_login_company(employee, co)
    res = client.post("/api/v1/reviews/policies/", data={}, content_type="application/json")
    assert res.status_code == 403


def test_reviews_disabled(make_user, make_company, make_membership, force_login_company):
    u = make_user(login_id="dis-3")
    co = make_company(code="co")
    make_membership(user=u, company=co, role="monitor", active=False)
    client = force_login_company(u, co)
    res = client.get("/api/v1/reviews/decisions/")
    assert res.status_code in (401, 403)


# --- exports ---


def test_exports_happy(make_user, make_company, force_login_company):
    owner = make_user(login_id="own-5")
    co = make_company(owner=owner, code="co")
    client = force_login_company(owner, co)
    res = client.get("/api/v1/exports/requests/")
    assert res.status_code == 200


def test_exports_cross_tenant(make_user, make_company, force_login_company):
    a = make_user(login_id="a-5")
    b = make_user(login_id="b-5")
    co_a = make_company(owner=a, code="co-a-5")
    co_b = make_company(owner=b, code="co-b-5")
    client = force_login_company(a, co_a)
    res = client.get(f"/api/v1/exports/requests/?company_id={co_b.id}")
    assert res.status_code in (403, 404)


def test_exports_role_mismatch(make_user, make_company, force_login_company):
    employee = make_user(login_id="emp-5")
    co = make_company(code="co")
    client = force_login_company(employee, co)
    res = client.post("/api/v1/exports/requests/", data={}, content_type="application/json")
    assert res.status_code == 403


def test_exports_disabled(make_user, make_company, make_membership, force_login_company):
    u = make_user(login_id="dis-5")
    co = make_company(code="co")
    make_membership(user=u, company=co, role="owner", active=False)
    client = force_login_company(u, co)
    res = client.get("/api/v1/exports/requests/")
    assert res.status_code in (401, 403)


def test_exports_no_company_in_session(make_user, force_login_company):
    u = make_user(login_id="no-co-5")
    client = force_login_company(u, None)  # type: ignore[arg-type]
    res = client.get("/api/v1/exports/requests/")
    assert res.status_code in (401, 403)


# --- backups ---


def test_backups_happy(make_user, make_company, force_login_company):
    owner = make_user(login_id="own-6")
    co = make_company(owner=owner, code="co")
    client = force_login_company(owner, co)
    res = client.get("/api/v1/backups/runs/")
    assert res.status_code == 200


def test_backups_cross_tenant(make_user, make_company, force_login_company):
    a = make_user(login_id="a-6")
    b = make_user(login_id="b-6")
    co_a = make_company(owner=a, code="co-a-6")
    co_b = make_company(owner=b, code="co-b-6")
    client = force_login_company(a, co_a)
    res = client.get(f"/api/v1/backups/runs/?company_id={co_b.id}")
    assert res.status_code in (403, 404)


def test_backups_run_owner_only(make_user, make_company, force_login_company):
    monitor = make_user(login_id="mon")
    co = make_company(code="co")
    client = force_login_company(monitor, co)
    res = client.post("/api/v1/backups/run/", data={}, content_type="application/json")
    assert res.status_code == 403


def test_backups_disabled(make_user, make_company, make_membership, force_login_company):
    u = make_user(login_id="dis-6")
    co = make_company(code="co")
    make_membership(user=u, company=co, role="owner", active=False)
    client = force_login_company(u, co)
    res = client.get("/api/v1/backups/runs/")
    assert res.status_code in (401, 403)


def test_backups_no_company_in_session(make_user, force_login_company):
    u = make_user(login_id="no-co-6")
    client = force_login_company(u, None)  # type: ignore[arg-type]
    res = client.get("/api/v1/backups/runs/")
    assert res.status_code in (401, 403)


# --- add more endpoints until ≥50 tests ---
```

### 2.2 Verify

```bash
cd backend
pytest -m permission --collect-only -q | Select-Object -Last 2
# Expected: ≥ 50
pytest -m permission
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## Step 3: Markers

`pyproject.toml` already has `permission` from QA-01. Confirm:

```bash
pytest --markers 2>&1 | Select-String -Pattern "permission"
# Expected: 1+ match
```

---

## Step 4: Docs

1. Update `docs/TEST_STRATEGY.md` with the new file under **Permission**.
2. Update `CHANGELOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Test file exists | `Test-Path backend\tests\test_tenant_isolation.py` | True |
| ≥50 tests | `pytest -m permission --collect-only` | ≥ 50 |
| All pass | `pytest -m permission` | 0 |
| `pytest -m "not slow"` | green | 0 |
| Docs updated | `grep test_tenant_isolation docs/TEST_STRATEGY.md` | match |

---

## Rollback

```bash
git revert <be03-commit-sha>
cd backend
pytest -m permission --collect-only -q
# Expected: < 50
```
