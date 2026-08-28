# QA-05: Verification Commands

> **Instructions:** Run baseline (Phase 1) before the change, then post-fix (Phase 2) to confirm ZAP, Bandit, Safety, and npm audit are wired in.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Confirm no ZAP config

```bash
Get-ChildItem -Recurse -Filter ".zap*" -ErrorAction SilentlyContinue
# Expected: 0 matches
```

### Command 1.2 — Confirm no ZAP in CI

```bash
Select-String -Path .github\workflows\*.yml -Pattern "zap"
# Expected: 0 matches
```

### Command 1.3 — Confirm no Bandit

```bash
Select-String -Path backend\pyproject.toml -Pattern "bandit"
# Expected: 0 matches
```

### Command 1.4 — Confirm no npm audit

```bash
Select-String -Path .github\workflows\*.yml -Pattern "npm audit"
# Expected: 0 matches
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — ZAP service in compose

```bash
Select-String -Path compose.dev.yml -Pattern "zap"
# Expected: 1+ match
```

### Command 2.2 — Bandit installed

```bash
cd backend
pip install bandit
bandit --version
# Expected: bandit x.y.z
```

### Command 2.3 — `zap-baseline` job present

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "zap-baseline"
# Expected: 1+ match
```

### Command 2.4 — `zap-full` weekly workflow

```bash
Get-Content .github\workflows\zap-full.yml | Select-String -Pattern "zap-full-scan"
# Expected: 1+ match

Get-Content .github\workflows\zap-full.yml | Select-String -Pattern "cron"
# Expected: 1+ match
```

### Command 2.5 — `dependency-audit` job present

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "bandit"
Get-Content .github\workflows\ci.yml | Select-String -Pattern "safety"
Get-Content .github\workflows\ci.yml | Select-String -Pattern "npm audit"
# Expected: 3 matches
```

### Command 2.6 — `fail-on-high-risk` script

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "fail"
# Expected: 1+ match (e.g., "if grep -q 'High'")
```

### Command 2.7 — Report artifacts

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "zap_report"
Get-Content .github\workflows\ci.yml | Select-String -Pattern "bandit"
Get-Content .github\workflows\ci.yml | Select-String -Pattern "safety"
# Expected: 3 matches
```

### Command 2.8 — Local ZAP baseline run

```bash
docker compose -f compose.dev.yml up -d backend zap
docker compose -f compose.dev.yml exec zap zap-baseline.py -t http://backend:8000 -r /tmp/zap.html -I
Test-Path /tmp/zap.html
# Expected: True (the report is generated)
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Bandit clean

```bash
cd backend
bandit -r apps -ll
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

### Command 3.2 — Safety clean

```bash
cd backend
safety check --full-report
echo "Exit code: $LASTEXITCODE"
# Expected: 0 (or documented exceptions)
```

### Command 3.3 — npm audit clean

```bash
cd frontend
npm audit --audit-level=high
echo "Exit code: $LASTEXITCODE"
# Expected: 0
```

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 / 1.4 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 / 2.6 / 2.7 / 2.8 green
- ✅ Command 3.1 / 3.2 / 3.3 local scans clean
