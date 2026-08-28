# FE-05: CSRF Integration — Goal

## Objective
Wire the frontend HTTP client to read Django's `csrftoken` cookie and
attach the `X-CSRFToken` header to every unsafe request so production
mutations succeed.

## Acceptance criteria
1. `getCsrfToken()` reads the `csrftoken` cookie.
2. `ensureCsrfToken()` pre-flights a safe request to guarantee a
   cookie exists.
3. The shared `api()` client sets `X-CSRFToken` for every
   `POST`/`PUT`/`PATCH`/`DELETE` request.
4. `credentials: "include"` is preserved on every request.
5. E2E specs cover the CSRF header on submit.
