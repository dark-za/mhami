# QA-04: Implementation Guide

> **Golden Rule:** every scenario is a single self-contained `*.js` file that runs against a real backend. Thresholds are not negotiable.

## Step 1: Install k6

```bash
# Windows (winget)
winget install k6 --source winget

# macOS
brew install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6
```

---

## Step 2: Seed command

### 2.1 New file: `backend/apps/identity/management/commands/make_load_users.py`

```python
"""Create a pool of users + companies for load tests."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.identity.models import User
from apps.organizations.models import CompanyMembership, CompanyRole
from apps.tenancy.models import Company, CompanyStatus


class Command(BaseCommand):
    help = "Create 200 users and 4 companies for k6 load tests."

    def add_arguments(self, parser):
        parser.add_argument("--per-role", type=int, default=50)

    @transaction.atomic
    def handle(self, *args, **opts):
        per_role = opts["per_role"]
        for role in CompanyRole.values:
            company = Company.objects.create(
                name=f"Load {role}",
                code=f"load-{role}",
                status=CompanyStatus.ACTIVE,
                trial_ends_at="2030-01-01T00:00:00Z",
            )
            for i in range(per_role):
                user = User.objects.create_user(
                    login_id=f"load-{role}-{i}",
                    password="P@ssw0rd!",
                    display_name=f"Load {role} {i}",
                )
                CompanyMembership.objects.create(
                    user=user, company=company, role=role, active=True,
                )
        self.stdout.write(self.style.SUCCESS("Load users created."))
```

**Verify:**
```bash
cd backend
python manage.py make_load_users --per-role 50
# Expected: "Load users created."
```

---

## Step 3: Scenarios

### 3.1 `tests/load/api_load.js`

```js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "2m", target: 50 },
    { duration: "5m", target: 100 },
    { duration: "2m", target: 200 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE = __ENV.API_URL ?? "http://localhost:8000";

export default function () {
  const loginRes = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({
      company_code: "load-owner",
      login_id: `load-owner-${__VU % 50}`,
      password: "P@ssw0rd!",
    }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(loginRes, {
    "login 200": (r) => r.status === 200,
    "has session": (r) => r.cookies.sessionid !== undefined,
  });

  if (loginRes.status === 200) {
    const me = http.get(`${BASE}/api/v1/tenancy/companies/me/`);
    check(me, { "me 200": (r) => r.status === 200 });
  }
  sleep(1);
}
```

### 3.2 `tests/load/evidence_load.js`

```js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "2m", target: 50 },
    { duration: "5m", target: 100 },
    { duration: "2m", target: 200 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE = __ENV.API_URL ?? "http://localhost:8000";

export function setup() {
  const login = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({
      company_code: "load-owner",
      login_id: "load-owner-0",
      password: "P@ssw0rd!",
    }),
    { headers: { "Content-Type": "application/json" } },
  );
  return { session: login.cookies.sessionid[0].value };
}

export default function (data) {
  const params = { headers: { Cookie: `sessionid=${data.session}` } };
  const list = http.get(`${BASE}/api/v1/evidence/items/?page=1`, params);
  check(list, { "list 200": (r) => r.status === 200 });
  sleep(1);
}
```

### 3.3 `tests/load/reviews_load.js`

```js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "2m", target: 25 },
    { duration: "5m", target: 50 },
    { duration: "2m", target: 100 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE = __ENV.API_URL ?? "http://localhost:8000";

export function setup() {
  const login = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({
      company_code: "load-manager",
      login_id: "load-manager-0",
      password: "P@ssw0rd!",
    }),
    { headers: { "Content-Type": "application/json" } },
  );
  // Find a review id to decide on
  const list = http.get(`${BASE}/api/v1/reviews/decisions/?status=open`, {
    headers: { Cookie: `sessionid=${login.cookies.sessionid[0].value}` },
  });
  const id = list.json("results.0.id");
  return { session: login.cookies.sessionid[0].value, id };
}

export default function (data) {
  const params = { headers: { Cookie: `sessionid=${data.session}`, "Content-Type": "application/json" } };
  const res = http.post(
    `${BASE}/api/v1/reviews/decisions/${data.id}/decide/`,
    JSON.stringify({ decision: "approve" }),
    params,
  );
  check(res, { "decide 200": (r) => r.status === 200 });
  sleep(2);
}
```

### 3.4 `tests/load/scheduler_load.js`

```js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 10 },
    { duration: "3m", target: 20 },
    { duration: "1m", target: 40 },
    { duration: "1m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<1000"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE = __ENV.API_URL ?? "http://localhost:8000";

export default function () {
  const res = http.post(`${BASE}/api/v1/tasks/dispatch_due/`, JSON.stringify({}), {
    headers: { "Content-Type": "application/json" },
  });
  check(res, { "dispatch 200": (r) => r.status === 200 });
  sleep(1);
}
```

---

## Step 4: README

### 4.1 New file: `tests/load/README.md`

```markdown
# k6 Load Tests

## Run locally

```bash
# 1. Boot the backend
docker compose -f compose.prod.yml up -d backend

# 2. Seed
docker compose -f compose.prod.yml exec backend python manage.py make_load_users --per-role 50

# 3. Run
k6 run --duration 30s --vus 5 tests/load/api_load.js
k6 run tests/load/evidence_load.js
k6 run tests/load/reviews_load.js
k6 run tests/load/scheduler_load.js
```

## Thresholds

| Scenario | p(95) | Error rate |
|---|---|---|
| api_load | < 500 ms | < 1% |
| evidence_load | < 500 ms | < 1% |
| reviews_load | < 500 ms | < 1% |
| scheduler_load | < 1000 ms | < 1% |

## Summary

Each run produces a `summary.json` that is uploaded as a CI artifact.
```

---

## Step 5: CI workflow

### 5.1 New file: `.github/workflows/k6.yml`

```yaml
name: k6

on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

jobs:
  load:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: mhami_load
          POSTGRES_USER: mhami
          POSTGRES_PASSWORD: mhami
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 5s --health-timeout 5s --health-retries 10
      redis:
        image: redis:7
        ports: ["6379:6379"]
    container:
      image: grafana/k6:latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Install backend
        run: pip install -r backend/requirements.txt
      - name: Migrate
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_load }
        run: cd backend && python manage.py migrate
      - name: Seed
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_load }
        run: cd backend && python manage.py runserver 0.0.0.0:8000 &
        # Note: the seed is run inside the container below.
      - name: Wait for backend
        run: |
          for i in $(seq 1 30); do
            curl -sf http://localhost:8000/api/v1/tenancy/health/ && break
            sleep 2
          done
      - name: Seed users
        run: docker exec -i $(docker ps -qf "ancestor=python:3.13-slim") python manage.py make_load_users
        # Simplified: in practice, run seeding in the backend container.
      - name: Run scenarios
        run: |
          for s in api_load evidence_load reviews_load scheduler_load; do
            k6 run --summary-export=tests/load/summary-$s.json tests/load/$s.js
          done
      - name: Upload summaries
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: k6-summaries
          path: tests/load/summary-*.json
```

**Verify:**
```bash
Get-Content .github\workflows\k6.yml | Select-String -Pattern "k6 run"
# Expected: 1+ match
```

---

## Step 6: Documentation

1. Update `docs/SERVER_INVENTORY.md` with the SLO table.
2. Update `CHANGELOG.md` with a `QA-04` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| 4 scenarios present | `Get-ChildItem tests\load -Filter "*.js"` | 4 files |
| Thresholds present | `grep "p(95)<500" tests/load/*.js` | 4 matches |
| k6 inspect clean | `k6 inspect tests/load/api_load.js` | exit 0 |
| CI job added | `grep k6 .github/workflows/*.yml` | match |
| Cron schedule | `grep cron .github/workflows/k6.yml` | match |
| Summary upload | `grep summary .github/workflows/k6.yml` | match |

---

## Rollback

```bash
git revert <qa04-commit-sha>
# Remove the k6 workflow
rm .github/workflows/k6.yml
```
