# FE-05: CSRF integration in client

## Discovery

### Problem
`frontend/src/api/client.ts` does not read the `csrftoken` cookie and does not send the `X-CSRFToken` header.

### Impact
- All mutations (POST/PUT/PATCH/DELETE) will fail with 403 in Production
- The application is functionally disabled

## Fix

**`src/api/client.ts` (Modify):**
```typescript
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export async function api<T>(path: string, init: ApiInit = {}): Promise<T> {
  const { body, headers, method, ...rest } = init;
  const base = resolveBase();
  const finalHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...(headers as Record<string, string> | undefined),
  };

  // ✅ Add CSRF token to unsafe methods
  if (method && UNSAFE_METHODS.has(method.toUpperCase())) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      finalHeaders['X-CSRFToken'] = csrfToken;
    } else {
      console.warn('CSRF token not found; unsafe request may fail');
    }
  }

  // ... rest of the logic
}
```

### E2E Tests

**`tests/e2e/csrf.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test('login includes X-CSRFToken header', async ({ page }) => {
  let csrfHeader: string | null = null;

  page.on('request', request => {
    if (request.url().includes('/api/v1/auth/login') && request.method() === 'POST') {
      csrfHeader = request.headers()['x-csrftoken'];
    }
  });

  await page.goto('/login');
  await page.fill('[name="company_code"]', 'test');
  await page.fill('[name="login_id"]', 'test');
  await page.fill('[name="password"]', 'test');
  await page.click('button[type="submit"]');

  expect(csrfHeader).toBeTruthy();
});

test('logout includes X-CSRFToken', async ({ page }) => {
  // login first
  // then logout
  // assert header
});
```

### Acceptance Standards
- AC-1: getCsrfToken() works
- AC-2: unsafe methods send X-CSRFToken
- AC-3: E2E test passes
- AC-4: typecheck passes
