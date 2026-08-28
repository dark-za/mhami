# QA-04: Verification Commands

> **Instructions:** Run baseline (Phase 1) before the change, then post-fix (Phase 2) to confirm the runner, scenarios, and CI job.

## Phase 1: Pre-Fix Proof

### Command 1.1 — Confirm no load tests

```bash
Test-Path tests\load
# Expected: False
```

### Command 1.2 — Confirm no k6 in CI

```bash
Select-String -Path .github\workflows\*.yml -Pattern "k6"
# Expected: 0 matches
```

### Command 1.3 — Confirm no k6 in compose

```bash
Select-String -Path compose.yml -Pattern "k6"
# Expected: 0 matches
```

---

## Phase 2: Post-Fix Verification

### Command 2.1 — `tests/load/` exists

```bash
Get-ChildItem tests\load -Filter "*.js" | Measure-Object | Select-Object -ExpandProperty Count
# Expected: 4
```

### Command 2.2 — Each scenario is syntactically valid

```bash
k6 inspect tests\load\api_load.js
k6 inspect tests\load\evidence_load.js
k6 inspect tests\load\reviews_load.js
k6 inspect tests\load\scheduler_load.js
# Expected: each prints the parsed script summary, exit 0
```

### Command 2.3 — Each scenario runs

```bash
k6 run --duration 10s --vus 5 tests\load\api_load.js
echo "Exit code: $LASTEXITCODE"
# Expected: 0 (or threshold-fail if infra is too small)
```

### Command 2.4 — Thresholds are present

```bash
Select-String -Path tests\load\*.js -Pattern "p\(95\)<500"
Select-String -Path tests\load\*.js -Pattern "rate<0\.01"
# Expected: 4 matches in p(95), 4 matches in rate
```

### Command 2.5 — JSON summary produced

```bash
k6 run --summary-export tests\load\summary-api.json tests\load\api_load.js
Test-Path tests\load\summary-api.json
# Expected: True
```

### Command 2.6 — CI job added

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "k6"
# Expected: 1+ match
```

### Command 2.7 — Nightly schedule

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "cron"
# Expected: 1+ match
```

### Command 2.8 — Artifact upload

```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "summary.json"
# Expected: 1+ match
```

---

## Phase 3: Regression / Safety

### Command 3.1 — Backend boots under load

```bash
docker compose -f compose.prod.yml up -d backend
k6 run --duration 30s --vus 50 tests/load/api_load.js
echo "Exit code: $LASTEXITCODE"
# Expected: 0 (or threshold-fail with documented cause)
```

### Command 3.2 — Nightly job visible in Actions

After merging, the `Actions` tab in GitHub shows the `k6` workflow with the `schedule` trigger.

---

## 4. Final Acceptance

- ✅ Command 1.1 / 1.2 / 1.3 baseline captured
- ✅ Command 2.1 / 2.2 / 2.3 / 2.4 / 2.5 green
- ✅ Command 2.6 / 2.7 / 2.8 CI job wired in
- ✅ Command 3.1 backend survives a 50-VU burst
