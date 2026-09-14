import { expect, test } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";
import { AppShell } from "../shell/AppShell";
import { bootstrapSnapshot, type CalendarPreference, type Locale } from "../design-system/tokens";
import { createFallbackState } from "../api/bootstrap";

test("renders foundation shell", () => {
  const fixture = {
    ...bootstrapSnapshot,
    company: { ...bootstrapSnapshot.company, name: "Test Organization" },
  };
  const html = renderToStaticMarkup(
    <MemoryRouter initialEntries={["/"]}>
      <AppShell
        bootstrap={createFallbackState(fixture)}
        loadError={null}
        locale={bootstrapSnapshot.company.locale as Locale}
        setLocale={() => undefined}
        calendar={"gregorian" as CalendarPreference}
        setCalendar={() => undefined}
        notifications={null}
        notificationsError={false}
        onLogout={async () => undefined}
      />
    </MemoryRouter>,
  );
  expect(html).not.toContain("تسجيل الدخول لمساحة العمل");
  expect(html).toContain("Test Organization");
});
