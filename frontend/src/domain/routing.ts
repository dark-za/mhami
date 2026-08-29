/** Role-based route table used by the workspace shell. */

import type { Role } from "../design-system/tokens";

export type WorkspaceRoute =
  | "/"
  | "/dashboard"
  | "/operations"
  | "/tasks"
  | "/evidence"
  | "/people"
  | "/reviews"
  | "/admin"
  | "/agent-access";

export const routePermissions: Record<Exclude<WorkspaceRoute, "/">, Role[]> = {
  "/dashboard": ["platform_admin", "owner", "monitor"],
  "/operations": ["platform_admin", "owner", "monitor"],
  "/tasks": ["platform_admin", "owner", "monitor", "employee"],
  "/evidence": ["platform_admin", "owner", "monitor", "employee"],
  "/people": ["platform_admin", "owner", "monitor"],
  "/reviews": ["platform_admin", "owner", "monitor"],
  "/admin": ["platform_admin", "owner"],
  "/agent-access": ["platform_admin", "owner"],
};

export function getWorkspaceRoute(pathname: string): WorkspaceRoute {
  if (pathname === "/" || pathname === "") {
    return "/";
  }
  if (pathname in routePermissions) {
    return pathname as WorkspaceRoute;
  }
  return "/";
}

export function routeTitle(locale: "ar" | "en", route: WorkspaceRoute): string {
  const titles: Record<WorkspaceRoute, { ar: string; en: string }> = {
    "/": { ar: "الملخص", en: "Summary" },
    "/dashboard": { ar: "لوحة القيادة", en: "Dashboard" },
    "/operations": { ar: "العمليات", en: "Operations" },
    "/tasks": { ar: "المهام", en: "Tasks" },
    "/evidence": { ar: "الأدلة", en: "Evidence" },
    "/people": { ar: "الأفراد", en: "People" },
    "/reviews": { ar: "المراجعات", en: "Reviews" },
    "/admin": { ar: "الإدارة", en: "Admin" },
    "/agent-access": { ar: "وصول MCP", en: "MCP Access" },
  };
  return locale === "ar" ? titles[route].ar : titles[route].en;
}

export function defaultRouteForRole(role: Role | null | undefined): WorkspaceRoute | "/login" {
  if (role === "owner" || role === "platform_admin") {
    return "/people";
  }
  if (role === "monitor") {
    return "/reviews";
  }
  if (role === "employee") {
    return "/tasks";
  }
  return "/login";
}
