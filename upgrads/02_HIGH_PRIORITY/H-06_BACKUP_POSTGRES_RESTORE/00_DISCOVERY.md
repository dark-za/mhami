# H-06: Backup restore to PostgreSQL

## Discovery

### Problem
`apps/backups/services.py:_restore_database` only restores to SQLite:
```python
database_path = target / "database.sqlite3"
```

### Impact
- No production-like restore test
- RTO/RPO not actually validated
- k8s claim in PHASE11 is false

### Fix

**File:** `apps/backups/services.py` (Add)

```python
import subprocess
from django.conf import settings

def _restore_to_postgres(target: Path, entries: dict, db_name: str) -> dict:
    """Restore backup to a PostgreSQL database for verification."""
    pg_config = settings.RESTORE_PG_CONFIG  # {host, port, user, password}

    # 1. Create empty database
    admin_conn = psycopg2.connect(
        host=pg_config["host"],
        port=pg_config["port"],
        user=pg_config["user"],
        password=pg_config["password"],
        database="postgres",
    )
    admin_conn.autocommit = True
    with admin_conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cur.execute(f"CREATE DATABASE {db_name}")
    admin_conn.close()

    # 2. Restore schema via Django migrations
    restore_conn = psycopg2.connect(
        host=pg_config["host"],
        port=pg_config["port"],
        user=pg_config["user"],
        password=pg_config["password"],
        database=db_name,
    )
    restore_conn.autocommit = True

    # 3. Use Django's loaddata
    payload = entries["database.json"].decode("utf-8")
    with restore_conn.cursor() as cur:
        for deserialized in serializers.deserialize("json", payload):
            save_via_psycopg2(cur, deserialized.object)

    # 4. Verify counts
    counts = {}
    with restore_conn.cursor() as cur:
        for label in expected_counts:
            table = label_to_table(label)
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[label] = cur.fetchone()[0]

    restore_conn.close()
    return counts
```

### Tests
```python
@pytest.mark.integration
def test_restore_to_postgres():
    # Requires test PG instance
    run = create_backup_run(company, owner)
    result = restore_backup_run(
        company, owner, str(run.id),
        target_name="pg_test", confirmation=f"RESTORE {run.id}",
    )
    # Verify data exists in PG
    pg_conn = psycopg2.connect(...)
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM companies")
        assert cur.fetchone()[0] == 1
```

### Acceptance Standards
- AC-1: restore to PostgreSQL works
- AC-2: counts match
- AC-3: integration test in CI
- AC-4: No regression in SQLite restore
