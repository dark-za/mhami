import { expect, test } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router";
import { AppShell } from "../shell/AppShell";
import { bootstrapSnapshot, type CalendarPreference, type Locale } from "../design-system/tokens";
import { createFallbackState } from "../api/bootstrap";

test("renders foundation shell", () => {
  const html = renderToStaticMarkup(
    <MemoryRouter initialEntries={["/"]}>
      <AppShell
        bootstrap={createFallbackState(bootstrapSnapshot)}
        setBootstrap={() => undefined}
        loading={false}
        loadError={null}
        locale={bootstrapSnapshot.company.locale as Locale}
        setLocale={() => undefined}
        calendar={"gregorian" as CalendarPreference}
        setCalendar={() => undefined}
        notifications={null}
        notificationsError={false}
      />
    </MemoryRouter>,
  );
  expect(html).toContain("Login and shell entry");
  expect(html).toContain("Nadi Foods");
});
