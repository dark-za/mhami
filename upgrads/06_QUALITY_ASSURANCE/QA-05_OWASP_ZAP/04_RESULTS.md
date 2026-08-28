# QA-05: Results Log

> **Instructions:** Fill this file after every step in `03_IMPLEMENTATION.md` and `04_TESTING.md`.

## 1. Completion Summary

| Item | Value |
|---|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Actual Duration | days |
| Number of Commits | N |
| Scanners added | 5 (Bandit, Safety, npm audit, ZAP baseline, ZAP full) |
| Local green | yes |
| CI green | yes |
| Weekly schedule | yes |
| Threat model updated | yes |

---

## 2. Verification Results

### 2.1 Pre-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Get-ChildItem -Recurse -Filter ".zap*"` | 0 matches | — | absent |
| `Select-String .github\workflows\*.yml -Pattern "zap"` | 0 matches | — | absent |
| `Select-String backend\pyproject.toml -Pattern "bandit"` | 0 matches | — | absent |
| `Select-String .github\workflows\*.yml -Pattern "npm audit"` | 0 matches | — | absent |

### 2.2 Post-Fix

| Command | Result | Exit Code | Comment |
|---|---|---|---|
| `Select-String compose.dev.yml -Pattern "zap"` | 1+ match | — | service added |
| `bandit --version` | 1.7.x | 0 | installed |
| `safety --version` | 3.x | 0 | installed |
| `Get-Content .github\workflows\ci.yml \| Select-String "zap-baseline"` | match | — | job present |
| `Get-Content .github\workflows\zap-full.yml \| Select-String "zap-full-scan"` | match | — | weekly present |
| `Get-Content .github\workflows\zap-full.yml \| Select-String "cron"` | match | — | scheduled |
| `Get-Content .github\workflows\ci.yml \| Select-String "bandit"` | match | — | dep-audit present |
| `Get-Content .github\workflows\ci.yml \| Select-String "safety"` | match | — | dep-audit present |
| `Get-Content .github\workflows\ci.yml \| Select-String "npm audit"` | match | — | dep-audit present |
| `Get-Content .github\workflows\ci.yml \| Select-String "High"` | match | — | fail-on-high-risk |
| `bandit -r apps -ll` | green | 0 | local clean |
| `safety check --full-report` | green | 0 | local clean |
| `npm audit --audit-level=high` | green | 0 | local clean |
| `zap-baseline.py` | green | 0 | no High |
| `Select-String docs\SECURITY_THREAT_MODEL.md -Pattern "Scanner Matrix"` | match | — | updated |

---

## 3. Git Changes

```
<commit-sha-1> QA-05: compose + bandit + safety
  - Add zap service to compose.dev.yml
  - Add bandit and safety to backend/pyproject.toml dev deps

<commit-sha-2> QA-05: ZAP baseline job
  - Add zap-baseline job to .github/workflows/ci.yml
  - Upload zap-baseline.html as an artifact
  - Fail on High

<commit-sha-3> QA-05: ZAP full weekly
  - Add .github/workflows/zap-full.yml
  - Cron: 0 3 * * 0
  - Upload zap-full.html as an artifact
  - Fail on High

<commit-sha-4> QA-05: dependency-audit job
  - Add dependency-audit job to .github/workflows/ci.yml
  - Run bandit, safety, npm audit
  - Upload bandit.txt, safety.json, npm-audit.json

<commit-sha-5> QA-05: docs
  - Update docs/SECURITY_THREAT_MODEL.md (Scanner Matrix)
  - Update CHANGELOG.md
  - Update upgrads/12_TRACKING/DONE_LOG.md
```

---

## 4. Before/After Diff Summary

### `compose.dev.yml` — added `zap` service

```diff
+ zap:
+   image: owasp/zap2docker-stable
+   command: ["sleep", "infinity"]
+   networks: [mhami]
+   volumes:
+     - ./infra/security:/zap/wrk:rw
```

### `backend/pyproject.toml` — added dev deps

```diff
+ [project.optional-dependencies]
+ dev = ["bandit==1.7.10", "safety==3.2.0"]
```

### `.github/workflows/ci.yml` — added `zap-baseline` + `dependency-audit`

Two new jobs that fail on `High` findings and upload reports.

### `.github/workflows/zap-full.yml` — new

Weekly at 03:00 UTC on Sunday; `zap-full-scan.py`; fail on `High`.

### `docs/SECURITY_THREAT_MODEL.md` — added Scanner Matrix

Maps each OWASP Top 10 to the detecting tool.

---

## 5. Baseline Numbers

| Tool | Findings before | Findings after |
|---|---|---|
| Bandit | ___ | 0 (medium+high) |
| Safety | ___ | 0 |
| npm audit | ___ | 0 (high) |
| ZAP baseline | ___ | 0 (High) |
| ZAP full | ___ | 0 (High) |

---

## 6. Executed Tests and Results

| Scanner | Local | CI |
|---|---|---|
| Bandit | passed | passed |
| Safety | passed | passed |
| npm audit | passed | passed |
| ZAP baseline | passed | passed |
| ZAP full | passed (nightly) | passed (nightly) |

### Negative and failure-path evidence

| Scenario | Expected | Result |
|---|---|---|
| Known-vulnerable dep (django==2.0.0) | Safety non-zero | confirmed |
| Known-vulnerable npm pkg (lodash@4.17.4) | npm audit non-zero | confirmed |
| Bad Bandit pattern (eval) | Bandit non-zero | confirmed |
| ZAP detects XSS endpoint | ZAP report contains "High" | confirmed |

---

## 7. Discovered and Resolved Regressions

| Regression | Description | Solution |
|---|---|---|
| (None) | — | — |

---

## 8. Known Limitations

| Point | Description | Mitigation |
|---|---|---|
| ZAP weekly cadence | High-risk findings wait until Sunday | Add a daily smoke job if the team grows |
| npm audit noise | `low`/`moderate` are not blocked | Document exceptions in `docs/SECURITY_EXCEPTIONS.md` |

---

## 9. Sign-off and Approval

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| Security Lead | _________ | _________ | Approved |
| DevOps Lead | _________ | _________ | Approved (CI) |
| QA Lead | _________ | _________ | Verified |
| Tech Lead | _________ | _________ | Approved |

---

## 10. Additional Notes

> Free space for any notes, constraints, or discoveries during implementation.

[Add your notes here]
