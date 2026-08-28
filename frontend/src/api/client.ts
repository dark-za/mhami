/**
 * Thin fetch wrapper used by every page in the shell.
 *
 * Centralises:
 *  - JSON content-type negotiation
 *  - `credentials: "include"` so session cookies flow through
 *  - CSRF token handling — every unsafe (POST/PUT/PATCH/DELETE) request
 *    reads the `csrftoken` cookie and sets the `X-CSRFToken` header so the
 *    server's `CsrfViewMiddleware` accepts the request.
 *  - Error parsing for DRF error envelopes (`{ detail | error: { code, message } }`)
 *
 * The wrapper throws an :class:`ApiError` with a machine-readable ``code`` so
 * callers can branch on ``error.code`` instead of inspecting strings.
 */

export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

const DEFAULT_BASE = "";

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function resolveBase(): string {
  // ``VITE_API_BASE`` may be set to a full origin (e.g. ``http://api:8000``)
  // in production deploys. When unset we use a relative origin so cookies
  // bind to the same host the SPA is served from.
  const env = (import.meta as ImportMeta & { env: Record<string, string> }).env;
  return env?.VITE_API_BASE ?? DEFAULT_BASE;
}

/**
 * Read the value of the ``csrftoken`` cookie set by Django's
 * ``CsrfViewMiddleware``.
 *
 * Returns ``null`` if the cookie is not present. The cookie is issued by
 * the first safe request the browser makes; the bootstrap call below
 * guarantees it exists before any mutation request is sent.
 */
export function getCsrfToken(): string | null {
  if (typeof document === "undefined" || !document.cookie) {
    return null;
  }
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Pre-flight bootstrap call that forces Django to set the ``csrftoken``
 * cookie on the current origin. Safe to call repeatedly; the server
 * returns 200 + cookie in both fresh-session and existing-session cases.
 */
export async function ensureCsrfToken(): Promise<void> {
  if (typeof document !== "undefined" && document.cookie.includes("csrftoken=")) {
    return;
  }
  await fetch(`${resolveBase()}/api/v1/bootstrap`, {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
  }).catch(() => {
    // If the bootstrap endpoint is unreachable the calling code will
    // surface a network error on the next mutation, which is the
    // intended behaviour.
  });
}

export interface ApiInit extends Omit<RequestInit, "body"> {
  body?: unknown;
}

export async function api<T>(path: string, init: ApiInit = {}): Promise<T> {
  const { body, headers, method, ...rest } = init;
  const base = resolveBase();
  const finalHeaders: Record<string, string> = {
    Accept: "application/json",
    ...(headers as Record<string, string> | undefined),
  };
  const httpMethod = (method ?? (body !== undefined ? "POST" : "GET")).toString().toUpperCase();

  // C-04: attach CSRF token to every unsafe request. If the cookie is
  // missing the request is allowed through (the server will reject it
  // with a 403) so the caller can refresh and retry; this is preferable
  // to silently re-issuing the cookie behind the caller's back.
  if (UNSAFE_METHODS.has(httpMethod)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      finalHeaders["X-CSRFToken"] = csrfToken;
    }
  }

  let finalBody: BodyInit | null | undefined;
  if (body !== undefined) {
    if (body instanceof FormData) {
      finalBody = body;
    } else {
      finalHeaders["Content-Type"] = "application/json";
      finalBody = JSON.stringify(body);
    }
  } else {
    finalBody = (rest as RequestInit & { body?: unknown }).body as BodyInit | null | undefined;
  }

  const response = await fetch(`${base}${path}`, {
    credentials: "include",
    ...rest,
    method: httpMethod,
    headers: finalHeaders,
    body: finalBody as BodyInit | null,
  });

  if (!response.ok) {
    const parsed = await response.json().catch(() => null);
    const code = parsed?.error?.code ?? (parsed?.detail ? "DRF_VALIDATION" : "UNKNOWN");
    const message =
      parsed?.error?.message ??
      parsed?.detail ??
      response.statusText ??
      `Request failed with ${response.status}`;
    throw new ApiError(code, message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
