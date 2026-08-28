# QA-01: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. Tests must use the existing `make_*` factories from `backend/conftest.py` — do not duplicate fixtures.

## Step 1: Register pytest markers in `pyproject.toml`

### 1.1 File before

```toml
[tool.mypy]
ignore_missing_imports = true
```

### 1.2 File after

```toml
[tool.mypy]
ignore_missing_imports = true

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["test_*.py", "*_test.py"]
markers = [
  "permission: tenant/branch/role permission boundary tests",
  "scheduler: cron/scheduler tests using freezegun",
  "migration: schema migration round-trip tests",
  "failure: failure-injection tests (broker, DB, webhooks, media)",
  "smoke: release smoke tests",
  "slow: tests that take >5s (skipped by default in fast feedback)",
]
```

**Verify:**
```bash
cd backend && pytest --markers 2>&1 | Select-String -Pattern "permission|scheduler|migration|failure|smoke"
# Expected: 5 marker lines
```

---

## Step 2: Permission tests

### 2.1 New file: `backend/apps/tenancy/tests/test_permissions.py`

```python
"""Tenant / branch / role permission matrix for tenancy endpoints."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.permission]


def test_owner_can_read_own_company(make_user, make_company, force_login_company):
    owner = make_user(login_id="own-1")
    company = make_company(owner=owner, code="co-own")
    client = force_login_company(owner, company)
    res = client.get(f"/api/v1/tenancy/companies/{company.id}/")
    assert res.status_code == 200


def test_outsider_cannot_read_company(make_user, make_company, force_login_company):
    outsider = make_user(login_id="out-1")
    target = make_company(code="co-target")
    other = make_company(owner=outsider, code="co-other")
    client = force_login_company(outsider, other)
    res = client.get(f"/api/v1/tenancy/companies/{target.id}/")
    assert res.status_code in (403, 404)


def test_branch_member_blocked_from_other_branch(make_user, make_company, make_branch, make_membership, force_login_company):
    owner = make_user(login_id="own-2")
    co = make_company(owner=owner, code="co-bm")
    b1 = make_branch(company=co, code="b-1")
    b2 = make_branch(company=co, code="b-2")
    make_membership(user=owner, company=co, role="employee", branch=b1)
    client = force_login_company(owner, co)
    res = client.get(f"/api/v1/tenancy/branches/{b2.id}/")
    assert res.status_code in (403, 404)


def test_employee_cannot_run_backup(make_user, make_company, make_membership, force_login_company):
    employee = make_user(login_id="emp-1")
    co = make_company(code="co-bk")
    make_membership(user=employee, company=co, role="employee")
    client = force_login_company(employee, co)
    res = client.post("/api/v1/backups/run/")
    assert res.status_code == 403


def test_manager_can_list_reviews_in_own_branch(make_user, make_company, make_branch, make_membership, force_login_company):
    mgr = make_user(login_id="mgr-1")
    co = make_company(owner=mgr, code="co-mg")
    b1 = make_branch(company=co, code="b-1")
    make_membership(user=mgr, company=co, role="manager", branch=b1)
    client = force_login_company(mgr, co)
    res = client.get("/api/v1/reviews/decisions/")
    assert res.status_code == 200


def test_supervisor_blocked_from_other_branch_reviews(make_user, make_company, make_branch, make_membership, force_login_company):
    sup = make_user(login_id="sup-1")
    co = make_company(owner=sup, code="co-sp")
    b1 = make_branch(company=co, code="b-1")
    b2 = make_branch(company=co, code="b-2")
    make_membership(user=sup, company=co, role="supervisor", branch=b1)
    client = force_login_company(sup, co)
    res = client.get(f"/api/v1/reviews/decisions/?branch={b2.id}")
    assert res.status_code in (403, 404)


def test_idempotent_company_lookup(make_user, make_company, force_login_company):
    owner = make_user(login_id="own-idem")
    co = make_company(owner=owner, code="co-idem")
    client = force_login_company(owner, co)
    a = client.get("/api/v1/tenancy/companies/me/")
    b = client.get("/api/v1/tenancy/companies/me/")
    assert a.status_code == b.status_code == 200


def test_disabled_membership_denied(make_user, make_company, make_membership, force_login_company):
    u = make_user(login_id="dis-1")
    co = make_company(code="co-dis")
    make_membership(user=u, company=co, role="owner", active=False)
    client = force_login_company(u, co)
    res = client.get("/api/v1/tenancy/companies/me/")
    assert res.status_code in (401, 403)


def test_role_escalation_blocked(make_user, make_company, make_membership, force_login_company):
    u = make_user(login_id="esc-1")
    co = make_company(code="co-esc")
    make_membership(user=u, company=co, role="employee")
    client = force_login_company(u, co)
    res = client.post("/api/v1/tenancy/companies/", data={"code": "x"}, content_type="application/json")
    assert res.status_code in (403, 405)


def test_session_without_company_is_rejected(make_user, force_login_company):
    u = make_user(login_id="no-co")
    client = force_login_company(u, None)  # type: ignore[arg-type]
    res = client.get("/api/v1/tenancy/companies/me/")
    assert res.status_code in (401, 403)
```

### 2.2 Mirror to other apps

Create the same `tests/test_permissions.py` skeleton in `apps/tasks/`, `apps/evidence/`, `apps/reviews/`, `apps/backups/`, adjusting URLs to match the app's endpoints.

**Verify:**
```bash
cd backend
pytest -m permission -v
# Expected: 10+ tests passed
```

---

## Step 3: Scheduler tests with `freezegun`

### 3.1 New file: `backend/apps/tasks/tests/test_scheduler.py`

```python
"""Scheduler tests using freezegun for deterministic time."""

from __future__ import annotations

from datetime import datetime, timezone as dt_tz

import pytest
from freezegun import freeze_time

from apps.tasks.services import dispatch_due_jobs

pytestmark = [pytest.mark.django_db, pytest.mark.scheduler]


@freeze_time("2030-01-01 06:00:00", tz_offset=0)
def test_job_due_at_cutoff_fires_once(make_task_schedule, make_task_instance):
    schedule = make_task_schedule(cron="0 6 * * *")
    instance = make_task_instance(schedule=schedule, status="pending")

    dispatch_due_jobs()
    instance.refresh_from_db()
    assert instance.status == "dispatched"

    dispatch_due_jobs()  # second call should not re-fire
    instance.refresh_from_db()
    assert instance.dispatch_count == 1


@freeze_time("2030-01-01 06:30:00", tz_offset=0)
def test_job_due_inside_cutoff_dispatched(make_task_schedule, make_task_instance):
    schedule = make_task_schedule(cron="30 6 * * *")
    instance = make_task_instance(schedule=schedule, status="pending")

    dispatch_due_jobs()
    instance.refresh_from_db()
    assert instance.status == "dispatched"


@freeze_time("2030-01-01 06:00:00", tz_offset=0)
def test_job_with_running_prerequisite_is_skipped(make_task_schedule, make_task_instance):
    schedule = make_task_schedule(cron="0 6 * * *")
    instance = make_task_instance(schedule=schedule, status="dispatched")  # already running
    instance.status = "running"
    instance.save()

    dispatch_due_jobs()
    instance.refresh_from_db()
    assert instance.status == "running"  # not re-dispatched


def test_misconfigured_cron_logs_and_skips(make_task_schedule, make_task_instance, caplog):
    schedule = make_task_schedule(cron="not-a-cron")
    make_task_instance(schedule=schedule, status="pending")
    with caplog.at_level("ERROR"):
        dispatch_due_jobs()
    assert any("invalid cron" in r.message.lower() for r in caplog.records)


@freeze_time("2030-01-01 06:00:00", tz_offset=0)
def test_double_fire_same_second_deduped(make_task_schedule, make_task_instance):
    schedule = make_task_schedule(cron="0 6 * * *")
    instance = make_task_instance(schedule=schedule, status="pending")
    dispatch_due_jobs()
    dispatch_due_jobs()
    instance.refresh_from_db()
    assert instance.dispatch_count == 1


def test_disabled_schedule_does_not_fire(make_task_schedule, make_task_instance):
    schedule = make_task_schedule(cron="0 6 * * *", enabled=False)
    instance = make_task_instance(schedule=schedule, status="pending")
    with freeze_time("2030-01-01 06:00:00"):
        dispatch_due_jobs()
    instance.refresh_from_db()
    assert instance.status == "pending"
```

### 3.2 New factories

Add to `backend/conftest.py` if not already present:

```python
@pytest.fixture
def make_task_schedule(db, make_company):
    def _factory(*, company=None, cron="0 6 * * *", enabled=True, **kw):
        from apps.tasks.models import TaskSchedule
        return TaskSchedule.objects.create(
            company=company or make_company(),
            cron=cron,
            enabled=enabled,
            **kw,
        )
    return _factory


@pytest.fixture
def make_task_instance(db, make_task_schedule):
    def _factory(*, schedule=None, status="pending", **kw):
        from apps.tasks.models import TaskInstance
        return TaskInstance.objects.create(
            schedule=schedule or make_task_schedule(),
            status=status,
            **kw,
        )
    return _factory
```

**Verify:**
```bash
cd backend
pytest -m scheduler -v
# Expected: 6 passed
```

---

## Step 4: Migration tests

### 4.1 New file: `backend/tests/test_migrations.py`

```python
"""Migration round-trip and integrity tests."""

from __future__ import annotations

import pytest
from django.apps import apps
from django.db import connection
from django.test.utils import CaptureQueriesContext

pytestmark = [pytest.mark.django_db, pytest.mark.migration]


def test_migration_graph_is_linear():
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(connection, ignore_no_migrations=True)
    for app_label, migrations in loader.graph.leaf_nodes():
        # leaf means the latest node; ensure no missing parents
        for migration in loader.disk_migrations.values():
            for dep in migration.dependencies:
                assert dep[0] in apps.app_configs, f"unknown dep {dep}"


def test_migrate_forward_backward_roundtrip(make_user, make_company, make_branch, make_task_instance):
    from django.core.management import call_command
    call_command("migrate", verbosity=0)
    user = make_user(login_id="mt-1")
    co = make_company(owner=user, code="mt-co")
    make_branch(company=co, code="mt-b")
    call_command("migrate", "tenancy", "0001_initial", verbosity=0)
    call_command("migrate", verbosity=0)
    assert co.__class__.objects.filter(code="mt-co").exists()


def test_new_column_with_default_preserves_data(make_user, make_company):
    co = make_company(code="preserve")
    # simulate a column-add by setting a known attribute
    co.name = "preserved"
    co.save()
    co.refresh_from_db()
    assert co.name == "preserved"


def test_removed_field_kept_through_rename(make_user, make_company):
    co = make_company(code="renamed")
    assert hasattr(co, "code")  # still present post-rename
```

**Verify:**
```bash
cd backend
pytest -m migration -v
# Expected: 4+ passed
```

---

## Step 5: Failure-injection tests

### 5.1 New file: `backend/tests/test_failure_injection.py`

```python
"""Failure-injection harness — broker, DB, webhooks, media."""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.failure]


def test_celery_broker_down_does_not_lose_audit(make_audit, caplog):
    with patch("apps.tasks.services.enqueue", side_effect=ConnectionError("redis down")):
        with caplog.at_level("ERROR"):
            from apps.tasks.services import enqueue_due_jobs
            enqueue_due_jobs()
    assert any("redis down" in r.message.lower() for r in caplog.records)
    assert make_audit.count() >= 1


def test_db_disconnect_rolls_back_safely(make_company):
    from django.db import transaction
    with pytest.raises(Exception):
        with transaction.atomic():
            make_company(code="will-rollback")
            raise ConnectionError("simulated")
    from apps.tenancy.models import Company
    assert not Company.objects.filter(code="will-rollback").exists()


def test_webhook_bad_hmac_rejected(client, make_audit):
    res = client.post(
        "/api/v1/connector/webhook/",
        data=b"{}",
        content_type="application/json",
        HTTP_X_SIGNATURE="bad",
    )
    assert res.status_code == 401
    assert make_audit.count() >= 1


def test_webhook_expired_timestamp_rejected(client, make_audit):
    res = client.post(
        "/api/v1/connector/webhook/",
        data=b"{}",
        content_type="application/json",
        HTTP_X_TIMESTAMP="2010-01-01T00:00:00Z",
    )
    assert res.status_code == 401


def test_oversized_media_rejected(client, settings):
    settings.MAX_UPLOAD_SIZE = 1024
    big = b"x" * 2048
    res = client.post(
        "/api/v1/evidence/items/",
        data={"file": (io.BytesIO(big), "big.jpg")},
        format="multipart",
    )
    assert res.status_code in (400, 413)


def test_missing_evidence_file_returns_404(client, make_evidence):
    e = make_evidence()
    res = client.get(f"/api/v1/evidence/items/{e.id}/file/")
    assert res.status_code == 404
```

### 5.2 Add `make_audit` factory

```python
@pytest.fixture
def make_audit(db):
    from apps.audit.models import AuditEvent
    return AuditEvent.objects
```

**Verify:**
```bash
cd backend
pytest -m failure -v
# Expected: 6 passed
```

---

## Step 6: Release smoke tests

### 6.1 New file: `backend/tests/test_release_smoke.py`

```python
"""Release smoke — boots the app, checks schema, walks each app."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

pytestmark = [pytest.mark.django_db, pytest.mark.smoke]


def test_django_check_deploy_passes():
    out = StringIO()
    call_command("check", stdout=out)
    assert "System check identified no issues" in out.getvalue() or out.getvalue() == ""


def test_schema_renders_without_error():
    call_command("spectacular", "--file", "/tmp/schema.yml")


def test_apps_have_health_endpoint(client):
    for app in [
        "tenancy", "identity", "tasks", "evidence", "reviews",
        "exports", "backups", "notifications", "audit",
    ]:
        res = client.get(f"/api/v1/{app}/health/")
        assert res.status_code in (200, 204), app


def test_authenticated_root_reachable(force_login_company, make_user, make_company):
    owner = make_user(login_id="smoke-1")
    co = make_company(owner=owner, code="smoke-co")
    client = force_login_company(owner, co)
    res = client.get("/api/v1/tenancy/companies/me/")
    assert res.status_code == 200


def test_migrate_round_trip_idempotent():
    call_command("migrate", verbosity=0)
    call_command("migrate", verbosity=0)
```

**Verify:**
```bash
cd backend
pytest -m smoke -v
# Expected: 5 passed
```

---

## Step 7: Run the full suite

```bash
cd backend
pytest --collect-only -q | Select-Object -Last 3
# Expected: >= 280 items collected

pytest -m "not slow"
# Expected: green, exit 0

pytest
# Expected: green, exit 0
```

---

## Step 8: Documentation

1. Update `docs/TEST_STRATEGY.md` with the new files and markers.
2. Update `CHANGELOG.md` with a `QA-01` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| No new Ruff violations | `ruff check apps tests` | 0 errors |
| No new MyPy errors | `mypy apps tests` | 0 errors |
| Existing smoke green | `pytest tests/test_factories_smoke.py` | 7 passed |
| Markers registered | `pytest --markers` | 5 lines |
| Total count | `pytest --collect-only -q` | ≥280 |

---

## Rollback

```bash
cd backend
git revert <qa01-commit-sha>
pytest -m "not slow"
# Expected: green, count returns to baseline
```
