# QA-05: Goal and Plan

## SMART Goal

> Within **1 week (5 working days)**, install **OWASP ZAP** (baseline + full),
> add **Bandit** (Python) and **Safety** (deps) and **npm audit** (frontend),
> and wire them into **3 CI jobs** that **fail the build on high-risk
> findings** and upload reports as artifacts.

## Detailed Acceptance Standards

### Standard 1: ZAP baseline (every PR)

`zap-baseline.py` runs against the staging URL (`http://api:8000` inside the compose network). It exits non-zero on **High** findings. The HTML report is uploaded as `zap-baseline.html`.

### Standard 2: ZAP full (weekly)

`zap-full-scan.py` runs weekly (`cron: '0 3 * * 0'`) against the same staging URL. The HTML report is uploaded as `zap-full.html`. The job fails on **High** findings.

### Standard 3: Dependency audit (every PR)

| Tool | Scope | Threshold |
|---|---|---|
| Bandit | `apps/` | `-ll` (medium + high) |
| Safety | `requirements.txt` | `--full-report`, fail on vulnerabilities |
| npm audit | `frontend/package.json` | `--audit-level=high` |

### Standard 4: Failure mode

All 3 jobs must call a final step that inspects the report and exits non-zero on a high-risk finding. Example for ZAP:

```bash
if grep -q "High" zap_report.html; then
  echo "::error::High risk findings"
  exit 1
fi
```

### Standard 5: Artifacts

| Job | Artifact | Path |
|---|---|---|
| zap-baseline | `zap-baseline.html` | `zap-baseline.html` |
| zap-full | `zap-full.html` | `zap-full.html` |
| dependency-audit | `bandit.txt`, `safety.json`, `npm-audit.json` | `*` |

### Standard 6: Compose service

`compose.dev.yml` must include a `zap` service:

```yaml
zap:
  image: owasp/zap2docker-stable
  command: ["sleep", "infinity"]
  networks: [mhami]
```

### Standard 7: Documentation

`docs/SECURITY_THREAT_MODEL.md` must include a **Scanner Matrix** section that maps each OWASP Top 10 category to the tool that detects it.

---

## Detailed Implementation Plan

### Day 1 — Compose + Bandit

**Morning**
- [ ] Add `zap` service to `compose.dev.yml`.
- [ ] Add `bandit` to `backend/pyproject.toml` dev deps.
- [ ] Run `bandit -r apps` and document baseline.

**Afternoon**
- [ ] Add a `bandit` step to the existing `ci.yml` job.

### Day 2 — Safety + npm audit

- [ ] Add `safety` to the dev deps.
- [ ] Add a `dependency-audit` job that runs `bandit`, `safety check`, and `npm audit --audit-level=high`.
- [ ] Document any exceptions in a new `docs/SECURITY_EXCEPTIONS.md`.

### Day 3 — ZAP baseline

- [ ] Add `zap-baseline` job to `ci.yml` (runs on every PR).
- [ ] Configure the `fail-on-high-risk` step.
- [ ] Upload `zap-baseline.html` as an artifact.

### Day 4 — ZAP full (weekly)

- [ ] Add `.github/workflows/zap-full.yml` with a weekly cron.
- [ ] Configure the same `fail-on-high-risk` step.
- [ ] Upload `zap-full.html` as an artifact.

### Day 5 — Docs

- [ ] Update `docs/SECURITY_THREAT_MODEL.md` with the scanner matrix.
- [ ] Update `CHANGELOG.md` and `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Dependency Graph

```
compose.dev.yml (zap)
    ↓
bandit + safety + npm audit
    ↓
ci.yml (zap-baseline + dependency-audit on every PR)
    ↓
zap-full.yml (weekly)
    ↓
docs/SECURITY_THREAT_MODEL.md
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | ZAP service boots; bandit runs | DevOps |
| CP-2 | `dependency-audit` job green | DevOps |
| CP-3 | `zap-baseline` job green | DevOps |
| CP-4 | `zap-full` weekly job green | DevOps |
| CP-5 | Threat model updated | Security Lead |
| CP-6 | Docs updated | Tech Writer |

---

## Cancellation Criteria

- If a ZAP false positive blocks the build → triage, fix the underlying issue, or document the exception in `docs/SECURITY_EXCEPTIONS.md`. Do not relax the threshold.
- If `safety check` requires a paid API key → fall back to `pip-audit` (open source).
