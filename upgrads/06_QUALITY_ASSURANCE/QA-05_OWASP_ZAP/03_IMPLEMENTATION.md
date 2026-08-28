# QA-05: Implementation Guide

> **Golden Rule:** scanners fail the build on high-risk findings. No exceptions, no skipped scans. Documented exceptions live in `docs/SECURITY_EXCEPTIONS.md`.

## Step 1: Add ZAP to `compose.dev.yml`

### 1.1 File before — `compose.dev.yml`

```yaml
services:
  backend:
    ...
  frontend:
    ...
```

### 1.2 File after

```yaml
services:
  backend:
    ...
  frontend:
    ...
  zap:
    image: owasp/zap2docker-stable
    command: ["sleep", "infinity"]
    networks: [mhami]
    volumes:
      - ./infra/security:/zap/wrk:rw
```

**Verify:**
```bash
Select-String -Path compose.dev.yml -Pattern "zap"
# Expected: 1+ match
```

---

## Step 2: Add Bandit to `backend/pyproject.toml`

### 2.1 File before

```toml
[project]
optional-dependencies = []
```

### 2.2 File after

```toml
[project.optional-dependencies]
dev = [
  "bandit==1.7.10",
  "safety==3.2.0",
]
```

```bash
cd backend
pip install -e ".[dev]"
bandit --version
safety --version
```

**Verify:**
```bash
bandit -r apps -ll
echo "Exit code: $LASTEXITCODE"
# Expected: 0 (baseline) or list of issues
```

---

## Step 3: ZAP baseline job in `ci.yml`

### 3.1 Add a new job

```yaml
  zap-baseline:
    runs-on: ubuntu-latest
    services:
      postgres: { ... }   # same as backend
      redis:    { ... }
    container:
      image: owasp/zap2docker-stable
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Install backend
        run: pip install -r backend/requirements.txt
      - name: Migrate
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_test }
        run: cd backend && python manage.py migrate
      - name: Start backend
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_test }
        run: cd backend && python manage.py runserver 0.0.0.0:8000 &
      - name: Wait for backend
        run: |
          for i in $(seq 1 30); do
            curl -sf http://localhost:8000/api/v1/tenancy/health/ && break
            sleep 2
          done
      - name: ZAP baseline
        run: |
          zap-baseline.py -t http://localhost:8000 -r /github/workspace/zap-baseline.html -I
      - name: Fail on high risk
        run: |
          if grep -q "High" zap-baseline.html; then
            echo "::error::High risk findings in ZAP baseline"
            exit 1
          fi
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: zap-baseline
          path: zap-baseline.html
```

**Verify:**
```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "zap-baseline"
# Expected: 1+ match
```

---

## Step 4: ZAP full (weekly)

### 4.1 New file: `.github/workflows/zap-full.yml`

```yaml
name: zap-full

on:
  schedule:
    - cron: "0 3 * * 0"
  workflow_dispatch:

jobs:
  zap-full:
    runs-on: ubuntu-latest
    services:
      postgres: { ... }
      redis:    { ... }
    container:
      image: owasp/zap2docker-stable
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Install backend
        run: pip install -r backend/requirements.txt
      - name: Migrate
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_test }
        run: cd backend && python manage.py migrate
      - name: Start backend
        env: { DATABASE_URL: postgres://mhami:mhami@localhost:5432/mhami_test }
        run: cd backend && python manage.py runserver 0.0.0.0:8000 &
      - name: Wait for backend
        run: |
          for i in $(seq 1 30); do
            curl -sf http://localhost:8000/api/v1/tenancy/health/ && break
            sleep 2
          done
      - name: ZAP full
        run: |
          zap-full-scan.py -t http://localhost:8000 -r /github/workspace/zap-full.html -I
      - name: Fail on high risk
        run: |
          if grep -q "High" zap-full.html; then
            echo "::error::High risk findings in ZAP full scan"
            exit 1
          fi
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: zap-full
          path: zap-full.html
```

**Verify:**
```bash
Get-Content .github\workflows\zap-full.yml | Select-String -Pattern "zap-full-scan"
Get-Content .github\workflows\zap-full.yml | Select-String -Pattern "cron"
# Expected: 1 match each
```

---

## Step 5: Dependency-audit job

### 5.1 Add to `ci.yml`

```yaml
  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - name: Install backend
        run: pip install -r backend/requirements.txt bandit safety
      - name: Bandit
        run: cd backend && bandit -r apps -ll -o bandit.txt -f txt
        continue-on-error: false
      - name: Safety
        run: cd backend && safety check --full-report --output safety.json
        continue-on-error: false
      - name: Install frontend
        run: npm ci --prefix frontend
      - name: npm audit
        run: cd frontend && npm audit --audit-level=high --json > npm-audit.json
        continue-on-error: false
      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dependency-audit
          path: |
            backend/bandit.txt
            backend/safety.json
            frontend/npm-audit.json
```

**Verify:**
```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "bandit"
Get-Content .github\workflows\ci.yml | Select-String -Pattern "safety"
Get-Content .github\workflows\ci.yml | Select-String -Pattern "npm audit"
# Expected: 3 matches
```

---

## Step 6: Threat model update

### 6.1 Append to `docs/SECURITY_THREAT_MODEL.md`

```markdown
## Scanner Matrix

| OWASP Top 10 | Tool | Where |
|---|---|---|
| A01 Broken Access Control | Bandit + ZAP + QA-01 permission tests | backend + compose |
| A02 Cryptographic Failures | Bandit (B303) + Safety | backend |
| A03 Injection (SQLi) | Bandit (B608) + ZAP | backend + compose |
| A04 Insecure Design | QA-01 + manual review | repo |
| A05 Security Misconfiguration | ZAP | compose |
| A06 Vulnerable Components | Safety + npm audit | backend + frontend |
| A07 Identification & Auth | QA-01 + QA-03 | backend + frontend |
| A08 Software & Data Integrity | Bandit + npm audit | backend + frontend |
| A09 Logging & Monitoring | QA-01 audit tests | backend |
| A10 SSRF | ZAP | compose |
```

**Verify:**
```bash
Select-String -Path docs\SECURITY_THREAT_MODEL.md -Pattern "Scanner Matrix"
# Expected: 1 match
```

---

## Step 7: Documentation

1. Update `CHANGELOG.md` with a `QA-05` entry.
2. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| ZAP in compose | `grep zap compose.dev.yml` | match |
| Bandit installed | `bandit --version` | exit 0 |
| ZAP baseline job | `grep zap-baseline .github/workflows/ci.yml` | match |
| ZAP full weekly | `grep zap-full-scan .github/workflows/zap-full.yml` | match |
| Cron schedule | `grep cron .github/workflows/zap-full.yml` | match |
| Dependency-audit job | `grep bandit .github/workflows/ci.yml` | match |
| Fail on high risk | `grep "High" .github/workflows/ci.yml` | match |
| Threat model | `grep "Scanner Matrix" docs/SECURITY_THREAT_MODEL.md` | match |

---

## Rollback

```bash
git revert <qa05-commit-sha>
rm .github/workflows/zap-full.yml
# Remove zap service from compose.dev.yml
docker compose -f compose.dev.yml up -d
```
