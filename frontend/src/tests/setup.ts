/**
 * Vitest global setup. Polyfills `matchMedia` and `IntersectionObserver`
 * which jsdom does not implement by default but which the app code may
 * reach in some branches.
 */
import { afterEach, beforeEach, vi } from "vitest";
import "../i18n";
import i18n from "../i18n";

afterEach(async () => {
  await i18n.changeLanguage("en");
});

beforeEach(async () => {
  window.localStorage.removeItem("mhami.locale");
  await i18n.changeLanguage("en");
});

if (typeof window !== "undefined" && !window.localStorage) {
  const values = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key) => values.get(key) ?? null,
    key: (index) => Array.from(values.keys())[index] ?? null,
    removeItem: (key) => values.delete(key),
    setItem: (key, value) => values.set(key, String(value)),
  };
  Object.defineProperty(window, "localStorage", { configurable: true, value: storage });
  Object.defineProperty(globalThis, "localStorage", { configurable: true, value: storage });
}

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

if (typeof window !== "undefined" && !("ResizeObserver" in window)) {
  (globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  };
}
