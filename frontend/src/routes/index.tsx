/**
 * AppRoutes — single route table consumed by `App.tsx`.
 *
 * `main.tsx` is the only place that mounts `<BrowserRouter>`. Routes are
 * code-split with `React.lazy()` so the initial bundle stays under the
 * performance budget. The route table itself stays eager because it is
 * tiny and is required for first-paint.
 */
import { Suspense, lazy, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router";

import { RoleGuard } from "../shell/RoleGuard";
import { RouteLoadingScreen } from "./RouteLoadingScreen";
import { useActiveRole } from "../hooks/useActiveRole";
import type { Role } from "../design-system/tokens";

const TasksPage = lazy(() => import("../pages/tasks/TasksPage"));
const EvidencePage = lazy(() => import("../pages/evidence/EvidencePage"));
const ReviewsPage = lazy(() => import("../pages/reviews/ReviewsPage"));
const PeoplePage = lazy(() => import("../pages/people/PeoplePage"));
const AIControlPage = lazy(() => import("../pages/admin/AIControlPage"));
const ExportsPage = lazy(() => import("../pages/operations/ExportsPage"));
const PilotPage = lazy(() => import("../pages/operations/PilotPage"));
const LoginPage = lazy(() => import("../pages/auth/LoginPage"));

const ALL_AUTHENTICATED_ROLES: Role[] = ["platform_admin", "owner", "monitor", "employee"];
const MONITOR_AND_ABOVE: Role[] = ["platform_admin", "owner", "monitor"];
const ADMIN_ONLY: Role[] = ["platform_admin", "owner"];

export interface AppRoutesProps {
  onTaskSelected?: (taskId: string) => void;
  activeTaskId?: string;
  activeLocale?: "ar" | "en";
  bootstrap?: import("../api/bootstrap").BootstrapState;
}

interface GuardedRouteProps {
  roles: Role[];
  children: ReactNode;
  resource: string;
  activeRole: Role;
}

function Guarded({ roles, activeRole, resource, children }: GuardedRouteProps) {
  return (
    <RoleGuard roles={roles} activeRole={activeRole} resource={resource}>
      {children}
    </RoleGuard>
  );
}

export function AppRoutes(props: AppRoutesProps) {
  const activeRole = useActiveRole();

  return (
    <Suspense fallback={<RouteLoadingScreen />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resource="Open the workspace from the navigation rail">
              <TasksPage onTaskSelected={props.onTaskSelected} />
            </Guarded>
          }
        />
        <Route
          path="/tasks"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resource="Tasks">
              <TasksPage onTaskSelected={props.onTaskSelected} />
            </Guarded>
          }
        />
        <Route
          path="/evidence"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resource="Evidence">
              <EvidencePage taskId={props.activeTaskId ?? ""} locale={props.activeLocale ?? "en"} />
            </Guarded>
          }
        />
        <Route
          path="/people"
          element={
            <Guarded roles={MONITOR_AND_ABOVE} activeRole={activeRole} resource="People">
              {props.bootstrap ? (
                <PeoplePage bootstrap={props.bootstrap} activeRole={activeRole} />
              ) : null}
            </Guarded>
          }
        />
        <Route
          path="/reviews"
          element={
            <Guarded roles={MONITOR_AND_ABOVE} activeRole={activeRole} resource="Reviews">
              <ReviewsPage />
            </Guarded>
          }
        />
        <Route
          path="/admin"
          element={
            <Guarded roles={ADMIN_ONLY} activeRole={activeRole} resource="Admin">
              <AIControlPage />
            </Guarded>
          }
        />
        <Route
          path="/operations"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resource="Operations">
              <ExportsPage />
            </Guarded>
          }
        />
        <Route
          path="/dashboard"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resource="Dashboard">
              <PilotPage />
            </Guarded>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
