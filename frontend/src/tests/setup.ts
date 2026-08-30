/**
 * Vitest global setup. Polyfills `matchMedia` and `IntersectionObserver`
 * which jsdom does not implement by default but which the app code may
 * reach in some branches.
 *
 * Unit tests use the application's i18n singleton and never contact a live API.
 */
import { beforeEach, vi } from "vitest";
import i18n from "../i18n";

const unexpectedFetch = vi.fn(async (input: RequestInfo | URL) => {
  throw new Error(`Unexpected network request in unit test: ${String(input)}`);
});

vi.stubGlobal("fetch", unexpectedFetch);

beforeEach(async () => {
  unexpectedFetch.mockClear();
  await i18n.changeLanguage("en");
});

// Polyfill matchMedia
if (typeof window !== "undefined" && !window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

// Polyfill IntersectionObserver
if (typeof window !== "undefined" && !("IntersectionObserver" in window)) {
  (globalThis as unknown as { IntersectionObserver: unknown }).IntersectionObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
    takeRecords(): unknown[] { return []; }
    root = null;
    rootMargin = "";
    thresholds = [];
  };
}

// Polyfill ResizeObserver
if (typeof window !== "undefined" && !("ResizeObserver" in window)) {
  (globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  };
}
