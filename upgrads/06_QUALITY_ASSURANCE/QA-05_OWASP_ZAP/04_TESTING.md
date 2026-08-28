# QA-05: Test Strategy

> **Rule:** every scanner in this file must run on a **real backend** (or its static codebase) and **fail the build** on high-risk findings.

## 1. Unit Tests

Not applicable — scanners are the tests.

## 2. Integration Tests

Not applicable.

## 3. End-to-End (Security Scan) Tests

### 3.1 Bandit (Python)

```bash
cd backend
bandit -r apps -ll -o bandit.txt -f txt
echo "Exit code: $LASTEXITCODE"
```

**Expected:** Exit code `0` (no medium/high findings). The report is saved to `bandit.txt`.

### 3.2 Safety (Python dependencies)

```bash
cd backend
safety check --full-report --output safety.json
echo "Exit code: $LASTEXITCODE"
```

**Expected:** Exit code `0` (no vulnerable deps).

### 3.3 npm audit (frontend)

```bash
cd frontend
npm audit --audit-level=high --json > npm-audit.json
echo "Exit code: $LASTEXITCODE"
```

**Expected:** Exit code `0` (no high-severity vulnerabilities).

### 3.4 ZAP baseline

```bash
docker compose -f compose.dev.yml up -d backend zap
docker compose -f compose.dev.yml exec zap zap-baseline.py -t http://backend:8000 -r /tmp/zap-baseline.html -I
grep -q "High" /tmp/zap-baseline.html && echo "High risk found" && exit 1
```

**Expected:** No "High" line in the report.

### 3.5 ZAP full

```bash
docker compose -f compose.dev.yml up -d backend zap
docker compose -f compose.dev.yml exec zap zap-full-scan.py -t http://backend:8000 -r /tmp/zap-full.html -I
grep -q "High" /tmp/zap-full.html && echo "High risk found" && exit 1
```

**Expected:** No "High" line in the report.

---

## 4. Success Criteria

| Tool | Scope | Threshold | CI |
|---|---|---|---|
| Bandit | `apps/` | `-ll` (medium + high) | green |
| Safety | `requirements.txt` | `--full-report` | green |
| npm audit | `frontend/package.json` | `--audit-level=high` | green |
| ZAP baseline | staging URL | no `High` in report | green |
| ZAP full | staging URL | no `High` in report | green |

---

## 5. Run Tests

### 5.1 Local (smoke)

```bash
# 1. Boot the backend
docker compose -f compose.dev.yml up -d backend

# 2. Bandit
cd backend
pip install bandit
bandit -r apps -ll

# 3. Safety
pip install safety
safety check --full-report

# 4. npm audit
cd ../frontend
npm audit --audit-level=high

# 5. ZAP baseline
docker compose -f compose.dev.yml up -d zap
docker compose -f compose.dev.yml exec zap zap-baseline.py -t http://backend:8000 -r /tmp/zap.html -I
```

### 5.2 CI

- `zap-baseline` runs on every PR.
- `zap-full` runs weekly (Sunday 03:00 UTC) and on `workflow_dispatch`.
- `dependency-audit` runs on every PR.

---

## 6. Failure simulation

To prove each scanner can fail the build:

| Tool | How to simulate | Expected exit |
|---|---|---|
| Bandit | `bandit -r apps -ll --confidence-level high` against a known bad file | non-zero |
| Safety | `pip install django==2.0.0 && safety check` | non-zero |
| npm audit | `npm install lodash@4.17.4` (historical CVE) | non-zero |
| ZAP | point at a service that returns `Server: Apache/2.2.15` | `High` in report |

Revert after each test.
