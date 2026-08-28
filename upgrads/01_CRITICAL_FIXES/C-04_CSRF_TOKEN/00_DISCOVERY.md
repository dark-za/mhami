# C-04: Fix CSRF in the Frontend (Missing X-CSRFToken)

## 1. Discovery Summary

### Current State

**Problem:** `frontend/src/api/client.ts` does not read the `csrftoken` cookie and does not send the `X-CSRFToken` header on mutation requests. Login and bootstrap also have raw `fetch` call sites outside the shared client. The plan must prove how the first CSRF cookie is issued before any unsafe request.

**Guide:**

`frontend/src/api/client.ts:39-64`:
```typescript
const response = await fetch(`${base}${path}`, {
  credentials: "include",
  ...rest,
  headers: finalHeaders,
  body: finalBody as BodyInit | null,
});
// ❌ No X-CSRFToken header
```

### Impact

| Dimension | Impact |
|---|---|
| Functional | Authenticated mutations can fail with 403 in Production |
| Security | Login CSRF and inconsistent protection are possible until the lifecycle is explicit |
| Operational | The application is functionally disabled |
| E2E | All submission tests will fail |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Reading csrftoken cookie | No | Yes (via `getCookie`) |
| Sending X-CSRFToken | No | Yes on every mutation |
| E2E mutation tests | 0 | ≥3 |
| Documentation | No | JSDoc in client.ts |

---

## 3. Goal

> Within **1 day**, add a helper to read the CSRF cookie and send it automatically in every unsafe request (POST/PATCH/PUT/DELETE).

### Acceptance Standards

1. AC-1: A documented first-load endpoint or response guarantees CSRF cookie issuance before unsafe same-origin requests.
2. AC-2: Login, register, bootstrap, logout, JSON, and multipart mutation calls use one client or an equivalent tested CSRF wrapper.
3. AC-3: Every unsafe request sends `X-CSRFToken`; missing-token requests fail locally or return an intentional server response.
4. AC-4: Browser tests prove first-load, login, logout, evidence upload, and policy mutation with Django CSRF checks enabled.
5. AC-5: Same-origin and configured cross-origin behavior are documented and tested; no browser test assumes a pre-existing cookie.

---

## 4. Sub-tasks

- [ ] Add `getCsrfToken()` helper and an explicit CSRF bootstrap path
- [ ] Move raw auth/bootstrap fetches to the shared authenticated client
- [ ] Update `api()` function to reject or report unsafe requests without a token
- [ ] Write first-load/login/logout/multipart mutation browser tests
- [ ] Run all tests

---

## 5. Implementation Code

**Design requirement:** Do not implement the snippet below in isolation. The
backend must explicitly issue the cookie, and every raw fetch call site must be
removed or covered by the same policy.

**File:** `frontend/src/api/client.ts` (Modify)

```typescript
function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export async function api<T>(path: string, init: ApiInit = {}): Promise<T> {
  const { body, headers, method, ...rest } = init;
  const base = resolveBase();
  const finalHeaders: Record<string, string> = {
    Accept: "application/json",
    ...(headers as Record<string, string> | undefined),
  };

  // ✅ CSRF: add token to unsafe methods
  if (method && UNSAFE_METHODS.has(method.toUpperCase())) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      finalHeaders["X-CSRFToken"] = csrfToken;
    }
  }

  let finalBody: BodyInit | null | undefined = ...;
  // ... rest unchanged
}
```

---

## 6. E2E Tests

**File:** `frontend/tests/e2e/csrf.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test('first-load obtains a CSRF cookie before login', async ({ page }) => {
  await page.goto('/login');
  const cookies = await page.context().cookies();
  const csrfCookie = cookies.find(c => c.name === 'csrftoken');
  expect(csrfCookie).toBeTruthy();

  // Submit login through the shared client and verify the actual response.
  await page.fill('[name="company_code"]', 'acme');
  await page.fill('[name="login_id"]', 'owner');
  await page.fill('[name="password"]', 'P@ssw0rd!');

  // Intercept the request to verify header
  const requestPromise = page.waitForRequest(req =>
    req.url().includes('/api/v1/auth/login') && req.method() === 'POST'
  );
  await page.click('button[type="submit"]');

  const req = await requestPromise;
  expect(req.headers()['x-csrftoken']).toBe(csrfCookie!.value);
});
```
