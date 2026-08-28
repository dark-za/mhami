# QA-05: Security Scanning (OWASP ZAP)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** There is **no automated security scanner** in the repository. There is no `.zap/` config, no `zap-baseline.py` invocation, and no `zap-full-scan.py` in CI. The platform is exposed to common web vulnerabilities (XSS, CSRF, header injection, outdated libraries) without any automated detection.

**Evidence gathered:**
- `compose.dev.yml` / `compose.prod.yml` does not include a ZAP service.
- `.github/workflows/` has no `zap` job.
- `docs/SECURITY_THREAT_MODEL.md` lists threats but does not link to a scanner.
- `backend/pyproject.toml` does not include `bandit` or `safety`; the frontend has no `npm audit` step.

### Impact

| Dimension | Impact |
|---|---|
| Functional | Common web vulnerabilities may ship undetected. |
| Security | No automated detection of OWASP Top 10. |
| Compliance | PDPL and Gate-D require automated security evidence. |
| Operational | A late-discovered CVE requires an emergency release. |
| Financial | Breach cost vs. scanner cost. |

### Reproducible Evidence

```bash
# 1. Confirm no ZAP config
Get-ChildItem -Recurse -Filter ".zap*" -ErrorAction SilentlyContinue
# Expected today: 0 matches

# 2. Confirm no ZAP in CI
Select-String -Path .github\workflows\*.yml -Pattern "zap"
# Expected today: 0 matches

# 3. Confirm no Bandit in backend
Select-String -Path backend\pyproject.toml -Pattern "bandit"
# Expected today: 0 matches

# 4. Confirm no npm audit step
Select-String -Path .github\workflows\*.yml -Pattern "npm audit"
# Expected today: 0 matches
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| OWASP ZAP baseline | none | `zap-baseline.py` against staging URL |
| OWASP ZAP full | none | weekly `zap-full-scan.py` |
| ZAP in CI | none | `zap-scan` job in `.github/workflows/ci.yml` |
| ZAP in compose | none | `zap` service in `compose.dev.yml` |
| Bandit (Python) | none | `bandit -r apps` in CI |
| Safety (deps) | none | `safety check` in CI |
| npm audit | none | `npm audit --audit-level=high` in CI |
| `fail_on_high_risk` | none | yes, in the CI script |
| Report archiving | none | `zap_report.html` uploaded as artifact |

---

## 3. Goal Statement

> Within **1 week (5 working days)**, install OWASP ZAP, add Bandit and npm audit, and wire **3 CI jobs** (`zap-baseline` on every PR, `zap-full-scan` weekly, and a `dependency-audit` job on every PR) — all **failing the build on high-risk findings**.

### Acceptance Criteria

1. **AC-1:** `compose.dev.yml` includes a `zap` service based on `owasp/zap2docker-stable`.
2. **AC-2:** `.github/workflows/ci.yml` includes a `zap-baseline` job that runs on every PR.
3. **AC-3:** `.github/workflows/zap-full.yml` (or a weekly job in `ci.yml`) runs `zap-full-scan.py` weekly.
4. **AC-4:** A `dependency-audit` job runs `bandit -r apps`, `safety check`, and `npm audit --audit-level=high` on every PR.
5. **AC-5:** All 3 jobs fail on high-risk findings.
6. **AC-6:** Reports are uploaded as CI artifacts (`zap_report.html`, `bandit.txt`, `safety.json`, `npm-audit.json`).
7. **AC-7:** `docs/SECURITY_THREAT_MODEL.md` is updated with the scanner matrix.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ZAP false positives break the build | High | High | Start with `zap-baseline`; review and tune before enabling `fail-on-high-risk` on `zap-full-scan`. |
| npm audit generates noise | Medium | Medium | Use `--audit-level=high` only; document exceptions in `.nvmrc`. |
| Safety requires an API key | Low | Medium | Use the open `--full-report` mode; no key needed. |
| ZAP container size slows CI | Medium | Low | Cache the image; only re-pull on weekly jobs. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `zap` service to `compose.dev.yml` | DevOps | not-started |
| 2 | Add `bandit` to `backend/pyproject.toml` dev deps | Backend | not-started |
| 3 | Run `bandit -r apps` locally; document baseline | Backend | not-started |
| 4 | Add `zap-baseline` job to `.github/workflows/ci.yml` | DevOps | not-started |
| 5 | Add `zap-full` weekly workflow | DevOps | not-started |
| 6 | Add `dependency-audit` job (bandit + safety + npm) | DevOps | not-started |
| 7 | Update `docs/SECURITY_THREAT_MODEL.md` | Security Lead | not-started |
| 8 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [docs/SECURITY_THREAT_MODEL.md](../../../docs/SECURITY_THREAT_MODEL.md)
- [docs/SECURITY_AND_DATA_BASELINE.md](../../../docs/SECURITY_AND_DATA_BASELINE.md)
- [compose.dev.yml](../../../compose.dev.yml)
- [.github/workflows/ci.yml](../../../.github/workflows/ci.yml)
