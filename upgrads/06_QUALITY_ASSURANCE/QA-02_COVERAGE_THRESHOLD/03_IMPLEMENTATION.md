# QA-02: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. Coverage thresholds must fail the build on regression.

## Step 1: Add coverage tool config to `backend/pyproject.toml`

### 1.1 File before

```toml
[tool.mypy]
ignore_missing_imports = true
```

### 1.2 File after

```toml
[tool.mypy]
ignore_missing_imports = true

[tool.coverage.run]
source = ["apps"]
omit = [
  "*/migrations/*",
  "*/tests/*",
  "*/admin.py",
  "*/asgi.py",
  "*/wsgi.py",
]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = false
exclude_lines = [
  "pragma: no cover",
  "raise NotImplementedError",
  "if __name__ == .__main__.:",
  "if settings.DEBUG:",
  "if TYPE_CHECKING:",
  "\\.\\.\\.",
]
```

**Verify:**
```bash
cd backend
pytest --cov=apps --cov-report=term 2>&1 | Select-Object -Last 10
# Expected: TOTAL line shows a percentage.
```

---

## Step 2: Run with `--cov-fail-under=85`

```bash
cd backend
pytest --cov=apps --cov-fail-under=85
echo "Exit code: $LASTEXITCODE"
# Expected: 0 (passes)
```

If exit code is `2` (fail-under), the test layer must be extended — see QA-01.

---

## Step 3: Produce XML + HTML reports

```bash
cd backend
pytest --cov=apps --cov-report=xml --cov-report=html
Test-Path coverage.xml
Test-Path htmlcov\index.html
# Expected: True True
```

**Add to `.gitignore`:** `htmlcov/`, `.coverage`, `coverage.xml` are already typically ignored — confirm.

---

## Step 4: CI workflow

### 4.1 New/updated file: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: mhami_test
          POSTGRES_USER: mhami
          POSTGRES_PASSWORD: mhami
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Coverage
        env:
          DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest --cov=apps --cov-report=xml --cov-fail-under=85
      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
          flags: backend
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install
        run: npm ci --prefix frontend
      - name: Test + coverage
        run: |
          cd frontend
          npm run test -- --coverage
      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./frontend/coverage/lcov.info
          flags: frontend
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}
```

**Verify:**
```bash
Get-Content .github/workflows/ci.yml | Select-String -Pattern "cov-fail-under"
# Expected: at least 1 match
```

---

## Step 5: Document the secret

Add to `docs/SECRET_MANAGEMENT.md`:

```markdown
| `CODECOV_TOKEN` | Codecov | CI | No | required |
```

**Verify:**
```bash
Select-String -Path docs\SECRET_MANAGEMENT.md -Pattern "CODECOV_TOKEN"
# Expected: 1 match
```

---

## Step 6: Frontend coverage config

### 6.1 File before — `frontend/vite.config.ts`

```ts
import { defineConfig } from "vite";
// no test config
```

### 6.2 File after

```ts
/// <reference types="vitest" />
import { defineConfig } from "vite";

export default defineConfig({
  // ... existing plugins / build ...
  test: {
    globals: true,
    environment: "jsdom",
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 65,
        statements: 70,
      },
    },
  },
});
```

### 6.3 Add a coverage script in `frontend/package.json`

```json
{
  "scripts": {
    "coverage": "vitest run --coverage"
  }
}
```

**Verify:**
```bash
cd frontend
npm run coverage
# Expected: thresholds enforced; non-zero exit if below.
```

---

## Step 7: Codecov badge in `README.md`

Insert at the top of `README.md` (just under the title):

```markdown
[![codecov](https://codecov.io/gh/<org>/<repo>/branch/main/graph/badge.svg)](https://codecov.io/gh/<org>/<repo>)
```

Replace `<org>/<repo>` with the actual path.

**Verify:**
```bash
Select-String -Path README.md -Pattern "codecov"
# Expected: at least 1 match
```

---

## Step 8: Documentation

1. Update `docs/TEST_STRATEGY.md` with the coverage floor.
2. Update `CHANGELOG.md` with a `QA-02` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Backend coverage ≥ 85% | `pytest --cov=apps --cov-fail-under=85` | exit 0 |
| Frontend coverage thresholds green | `npm run coverage` | exit 0 |
| CI step present | `grep cov-fail-under .github/workflows/*.yml` | match |
| Codecov upload configured | `grep codecov .github/workflows/*.yml` | match |
| Badge present | `grep codecov README.md` | match |
| Secret documented | `grep CODECOV_TOKEN docs/SECRET_MANAGEMENT.md` | match |

---

## Rollback

```bash
cd backend
git revert <qa02-commit-sha>
pytest --cov=apps
# Expected: coverage reverts to baseline, no fail-under.
```
