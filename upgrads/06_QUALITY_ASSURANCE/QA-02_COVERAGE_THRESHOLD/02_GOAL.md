# QA-02: Goal and Plan

## SMART Goal

> Within **3 working days**, configure backend coverage (`fail_under=85`)
> and frontend coverage (`lines/functions ≥ 70`, `branches ≥ 65`),
> wire both into CI with **Codecov upload**, and surface a Codecov badge
> in `README.md`.

## Detailed Acceptance Standards

### Standard 1: Backend coverage config

`backend/pyproject.toml` must include:

```toml
[tool.coverage.run]
source = ["apps"]
omit = [
  "*/migrations/*",
  "*/tests/*",
  "*/admin.py",
]

[tool.coverage.report]
fail_under = 85
exclude_lines = [
  "pragma: no cover",
  "raise NotImplementedError",
  "if __name__ == .__main__.:",
  "if settings.DEBUG:",
  "if TYPE_CHECKING:",
]
```

**Verify:**
```bash
cd backend
pytest --cov=apps --cov-fail-under=85
# Expected: exit 0, summary >= 85%
```

### Standard 2: CI integration

`.github/workflows/ci.yml` must include a `coverage` step that:

1. Runs `pytest --cov=apps --cov-report=xml --cov-fail-under=85`.
2. Uploads `coverage.xml` to Codecov (`codecov/codecov-action@v4`).
3. Fails the build when `fail_under` is not met.

**Verify:**
```bash
Get-Content .github/workflows/ci.yml | Select-String -Pattern "cov-fail-under"
# Expected: at least 1 match
```

### Standard 3: Frontend coverage config

`frontend/vite.config.ts` must include:

```ts
test: {
  coverage: {
    provider: "v8",
    reporter: ["text", "html", "lcov"],
    thresholds: { lines: 70, functions: 70, branches: 65 },
  },
}
```

**Verify:**
```bash
cd frontend
npm run test -- --coverage
# Expected: thresholds enforced; non-zero exit if below.
```

### Standard 4: Badge + visibility

`README.md` must include a Codecov badge:

```markdown
[![codecov](https://codecov.io/gh/<org>/<repo>/branch/main/graph/badge.svg)](https://codecov.io/gh/<org>/<repo>)
```

**Verify:**
```bash
Select-String -Path README.md -Pattern "codecov"
# Expected: 1+ match
```

### Standard 5: Coverage artifacts

- `backend/coverage.xml`
- `backend/htmlcov/index.html`
- `frontend/coverage/lcov.info`

All three are uploaded to Codecov as separate flags (`backend`, `frontend`).

### Standard 6: Secret handling

`CODECOV_TOKEN` is declared in `docs/SECRET_MANAGEMENT.md` and stored only in the CI secrets store — never in compose, never in `.env.example`.

---

## Detailed Implementation Plan

### Day 1 — Backend config + baseline

**Morning**
- [ ] Add `[tool.coverage.run]` and `[tool.coverage.report]` to `pyproject.toml`.
- [ ] Run `pytest --cov=apps --cov-report=term` and capture the baseline.
- [ ] If baseline < 85%, file follow-up issues (cross-link to QA-01).

**Afternoon**
- [ ] Run `pytest --cov=apps --cov-fail-under=85` and confirm exit 0.
- [ ] Commit the config.

### Day 2 — CI + Codecov

**Morning**
- [ ] Update `.github/workflows/ci.yml` with the coverage step and Codecov upload.
- [ ] Document `CODECOV_TOKEN` in `docs/SECRET_MANAGEMENT.md`.

**Afternoon**
- [ ] Open a PR; verify Codecov receives the upload.
- [ ] Verify the badge URL is reachable.

### Day 3 — Frontend + docs

**Morning**
- [ ] Update `frontend/vite.config.ts` with `coverage.thresholds`.
- [ ] Add `coverage` script to `frontend/package.json`.
- [ ] Run `npm run test -- --coverage` and capture the baseline.

**Afternoon**
- [ ] Update `README.md` with the Codecov badge.
- [ ] Update `docs/TEST_STRATEGY.md` and `CHANGELOG.md`.

---

## Dependency Graph

```
pyproject.toml  ──→  baseline run  ──→  fail-under run
                                      │
                                      ↓
                              GitHub Actions
                                      │
                                      ↓
                              Codecov upload
                                      │
                                      ↓
                              Badge in README
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Backend config merged; baseline captured | Backend |
| CP-2 | `pytest --cov-fail-under=85` green | Backend |
| CP-3 | CI runs the coverage step | DevOps |
| CP-4 | Codecov upload visible | DevOps |
| CP-5 | Frontend thresholds green | Frontend |
| CP-6 | Badge added | Tech Writer |

---

## Cancellation Criteria

- If baseline < 85% after QA-01 has been implemented → re-open the test-layer plan.
- If Codecov is not available in the target environment → fall back to a local badge (`coverage.svg` from `coverage-badge`).
- If CI secret cannot be created → keep the upload step in the workflow but mark it as `continue-on-error` and open a follow-up.
