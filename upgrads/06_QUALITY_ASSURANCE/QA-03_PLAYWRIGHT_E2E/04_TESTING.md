# QA-03: Test Strategy

> **Rule:** every test in this file must pass against a real backend (`compose.dev.yml` + seeded data) before the upgrade is considered done.

## 1. Unit Tests

Not applicable — QA-03 is a browser-automation upgrade, not a feature.

## 2. Integration Tests

Not applicable.

## 3. End-to-End Tests

### 3.1 Authentication (`01_auth.spec.ts`)

| Test | Expected |
|---|---|
| `login success` | owner reaches `/` |
| `wrong password` | `[data-testid="login-error"]` visible |
| `locked account` | error contains "locked" |
| `CSRF token present` | `csrfmiddlewaretoken` input exists |
| `logout returns to /login` | URL is `/login` after `logout()` |

### 3.2 Navigation (`02_navigation.spec.ts`)

| Test | Expected |
|---|---|
| `/` → `/tasks` → `/evidence` → `/people` → `/reviews` → `/admin` → `/operations` → `/dashboard` | each URL matches |

### 3.3 Evidence (`03_evidence.spec.ts`)

| Test | Expected |
|---|---|
| upload happy | success toast |
| oversized | error contains "too large" |
| signature mismatch | error contains "signature" |
| missing CSRF | error contains "csrf" |
| list page | heading contains "evidence" |
| detail page | URL matches `/evidence/{id}/` |

### 3.4 Reviews (`04_reviews.spec.ts`)

| Test | Expected |
|---|---|
| open decision | URL matches `/reviews/{id}/` |
| approve | status contains "approved" |
| reject with reason | status contains "rejected" |
| comment | comments contain the new text |
| history | `[data-testid="history"]` is visible |

### 3.5 Roles (`05_roles.spec.ts`)

| Test | Expected |
|---|---|
| owner → /admin | allowed |
| employee → /admin | redirected away |
| manager → /people | allowed |
| supervisor → /reviews | no approve button |
| outsider → /admin | redirected to /login |

### 3.6 Locale (`06_locale.spec.ts`)

| Test | Expected |
|---|---|
| English | `dir="ltr"`, `lang="en"` |
| Arabic | `dir="rtl"`, `lang="ar"` |
| Hijri persists | calendar indicator shows "hijri" |
| Gregorian persists | calendar indicator shows "gregorian" |

---

## 4. Success Criteria

| Spec file | Tests | Pass rate |
|---|---|---|
| `01_auth.spec.ts` | 5 | 100% |
| `02_navigation.spec.ts` | 7 | 100% |
| `03_evidence.spec.ts` | 6 | 100% |
| `04_reviews.spec.ts` | 5 | 100% |
| `05_roles.spec.ts` | 5 | 100% |
| `06_locale.spec.ts` | 4 | 100% |
| **Total** | **≥30** | **100%** |

---

## 5. Run Tests

### 5.1 Local

```bash
# 1. Start the backend
cd compose
docker compose -f compose.dev.yml up -d backend
cd ../frontend

# 2. Run
npx playwright test --reporter=line
```

### 5.2 Single spec

```bash
cd frontend
npx playwright test tests/e2e/03_evidence.spec.ts --reporter=line
```

### 5.3 UI mode

```bash
cd frontend
npx playwright test --ui
```

### 5.4 CI

The `e2e` job in `.github/workflows/ci.yml` runs on every push and PR. The HTML report is uploaded as an artifact.

---

## 6. Failure simulation

To prove the runner can detect failures, intentionally break a test:

```bash
cd frontend
# Edit 02_navigation.spec.ts and change /tasks → /wrong-route
npx playwright test 02_navigation.spec.ts
echo "Exit code: $LASTEXITCODE"
# Expected: 1
```

Revert the change afterwards.
