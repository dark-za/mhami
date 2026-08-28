export type Locale = "ar" | "en";
export type CalendarPreference = "gregorian" | "hijri";
export type Role = "platform_admin" | "owner" | "monitor" | "employee";

export type NavModule = "dashboard" | "operations" | "tasks" | "evidence" | "people" | "reviews" | "admin";

export type NavItem = {
  module: NavModule;
  href: string;
  labelAr: string;
  labelEn: string;
  roles: Role[];
};

export type NotificationItem = {
  id: string;
  titleAr: string;
  titleEn: string;
  bodyAr: string;
  bodyEn: string;
  tone: "neutral" | "success" | "warning" | "danger";
};

export type BootstrapSnapshot = {
  currentUser: {
    id: string;
    displayName: string;
    loginId: string;
    role: Role;
    authenticated: boolean;
  };
  company: {
    name: string;
    code: string;
    status: string;
    locale: Locale;
    timezone: string;
    branding: {
      primary: string;
      secondary: string;
      accent: string;
    };
  };
  permissions: string[];
  enabledModules: NavModule[];
};

export const roleLabels: Record<Role, { ar: string; en: string }> = {
  platform_admin: { ar: "مدير المنصة", en: "Platform Admin" },
  owner: { ar: "المالك", en: "Owner" },
  monitor: { ar: "مراقب الجودة", en: "Quality Monitor" },
  employee: { ar: "موظف", en: "Employee" },
};

export const navItems: NavItem[] = [
  { module: "dashboard", href: "#dashboard", labelAr: "لوحة القيادة", labelEn: "Dashboard", roles: ["platform_admin", "owner", "monitor", "employee"] },
  { module: "operations", href: "#operations", labelAr: "العمليات", labelEn: "Operations", roles: ["platform_admin", "owner", "monitor", "employee"] },
  { module: "tasks", href: "#tasks", labelAr: "المهام", labelEn: "Tasks", roles: ["platform_admin", "owner", "monitor", "employee"] },
  { module: "evidence", href: "#evidence", labelAr: "الأدلة", labelEn: "Evidence", roles: ["platform_admin", "owner", "monitor", "employee"] },
  { module: "people", href: "#people", labelAr: "الأفراد", labelEn: "People", roles: ["platform_admin", "owner", "monitor"] },
  { module: "reviews", href: "#reviews", labelAr: "المراجعات", labelEn: "Reviews", roles: ["platform_admin", "owner", "monitor"] },
  { module: "admin", href: "#admin", labelAr: "الإدارة", labelEn: "Admin", roles: ["platform_admin", "owner"] },
];

export const notificationSeed: NotificationItem[] = [
  {
    id: "policy",
    titleAr: "تحديث سياسة الامتثال",
    titleEn: "Compliance policy updated",
    bodyAr: "تم تسجيل قبول قانوني جديد للمالك مع إمكانية التتبع الكامل.",
    bodyEn: "A new legal acceptance was recorded for the owner with full traceability.",
    tone: "success",
  },
  {
    id: "shift",
    titleAr: "تغيير في الوردية",
    titleEn: "Shift change",
    bodyAr: "أُضيفت وردية أسبوعية جديدة للموقع الرئيسي.",
    bodyEn: "A new weekly shift was added for the main branch.",
    tone: "neutral",
  },
  {
    id: "security",
    titleAr: "تأكيد MFA مطلوب",
    titleEn: "MFA confirmation required",
    bodyAr: "تفعيل TOTP متاح الآن للمديرين والمالكين.",
    bodyEn: "TOTP enrollment is available now for owners and admins.",
    tone: "warning",
  },
];

// C-14: the static bootstrap snapshot is used only as a transient placeholder
// for shape validation. It is no longer treated as an authenticated session.
// The `authenticated` flag is `false` so the workspace must not render any
// privileged UI before the real `/api/v1/bootstrap` response arrives, and
// test fixtures that previously relied on `authenticated: true` now have to
// mock the API response explicitly.
export const bootstrapSnapshot: BootstrapSnapshot = {
  currentUser: {
    id: "user-001",
    displayName: "Amina Hassan",
    loginId: "amina",
    role: "owner",
    authenticated: false,
  },
  company: {
    name: "Nadi Foods",
    code: "nadi-foods",
    status: "trial",
    locale: "ar",
    timezone: "Asia/Riyadh",
    branding: {
      primary: "#0f766e",
      secondary: "#111827",
      accent: "#f97316",
    },
  },
  permissions: [],
  enabledModules: [],
};

export function getVisibleNavItems(role: Role, enabledModules: NavModule[]): NavItem[] {
  return navItems.filter((item) => item.roles.includes(role) && enabledModules.includes(item.module));
}

export function formatLocalizedDate(date: Date, locale: Locale, calendar: CalendarPreference): string {
  const localeTag = locale === "ar" ? `ar-SA-u-ca-${calendar === "hijri" ? "islamic-umalqura" : "gregory"}` : `en-US-u-ca-${calendar === "hijri" ? "islamic-umalqura" : "gregory"}`;
  return new Intl.DateTimeFormat(localeTag, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
}

function clamp(value: number): number {
  return Math.max(0, Math.min(255, value));
}

function hexToRgb(hex: string): [number, number, number] {
  const normalized = hex.replace("#", "").trim();
  const expanded = normalized.length === 3 ? normalized.split("").map((part) => part + part).join("") : normalized;
  const value = Number.parseInt(expanded, 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function relativeLuminance([red, green, blue]: [number, number, number]): number {
  const convert = (channel: number) => {
    const normalized = channel / 255;
    return normalized <= 0.03928 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * convert(red) + 0.7152 * convert(green) + 0.0722 * convert(blue);
}

export function readableTextColor(hex: string): string {
  return relativeLuminance(hexToRgb(hex)) > 0.45 ? "#111827" : "#ffffff";
}

export function tintedSurface(hex: string, strength = 0.18): string {
  const [red, green, blue] = hexToRgb(hex);
  const mix = (channel: number) => clamp(Math.round(channel + (255 - channel) * strength));
  return `rgb(${mix(red)} ${mix(green)} ${mix(blue)})`;
}
