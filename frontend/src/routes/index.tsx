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
import { defaultRouteForRole } from "../domain/routing";

const TasksPage = lazy(() => import("../pages/tasks/TasksPage"));
const EvidencePage = lazy(() => import("../pages/evidence/EvidencePage"));
const ReviewsPage = lazy(() => import("../pages/reviews/ReviewsPage"));
const PeoplePage = lazy(() => import("../pages/people/PeoplePage"));
const AIControlPage = lazy(() => import("../pages/admin/AIControlPage"));
const AgentAccessPage = lazy(() => import("../pages/admin/AgentAccessPage"));
const ExportsPage = lazy(() => import("../pages/operations/ExportsPage"));
const LoginPage = lazy(() => import("../pages/auth/LoginPage"));
const SetupPage = lazy(() => import("../pages/auth/SetupPage"));
const DashboardPage = lazy(() => import("../pages/DashboardPage"));

const ALL_AUTHENTICATED_ROLES: Role[] = ["owner", "monitor", "employee"];
const MONITOR_AND_ABOVE: Role[] = ["owner", "monitor"];
const ADMIN_ONLY: Role[] = ["owner"];

export interface AppRoutesProps {
  onTaskSelected?: (taskId: string) => void;
  activeTaskId?: string;
  activeLocale?: "ar" | "en";
  bootstrap?: import("../api/bootstrap").BootstrapState;
  bootstrapLoading?: boolean;
}

interface GuardedRouteProps {
  roles: Role[];
  children: ReactNode;
  resourceKey: string;
  activeRole: Role | null;
}

function Guarded({ roles, activeRole, resourceKey, children }: GuardedRouteProps) {
  return (
    <RoleGuard roles={roles} activeRole={activeRole} resourceKey={resourceKey}>
      {children}
    </RoleGuard>
  );
}

export function AppRoutes(props: AppRoutesProps) {
  const activeRole = useActiveRole(props.bootstrap);
  if (props.bootstrapLoading) {
    return <RouteLoadingScreen />;
  }
  const authenticated =
    props.bootstrap?.source === "live" &&
    props.bootstrap.snapshot.currentUser.authenticated === true;
  const setupRequired =
    props.bootstrap?.source === "live" && props.bootstrap.setupRequired === true;

  if (!authenticated) {
    return (
      <Suspense fallback={<RouteLoadingScreen />}>
        <Routes>
          <Route path="/login" element={setupRequired ? <Navigate to="/setup" replace /> : <LoginPage />} />
          <Route path="/setup" element={setupRequired ? <SetupPage /> : <Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to={setupRequired ? "/setup" : "/login"} replace />} />
        </Routes>
      </Suspense>
    );
  }

  return (
    <Suspense fallback={<RouteLoadingScreen />}>
      <Routes>
        <Route path="/login" element={<Navigate to={defaultRouteForRole(activeRole)} replace />} />
        <Route path="/setup" element={<Navigate to={defaultRouteForRole(activeRole)} replace />} />

        <Route
          path="/"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resourceKey="nav.tasks">
              <TasksPage onTaskSelected={props.onTaskSelected} bootstrap={props.bootstrap} />
            </Guarded>
          }
        />
        <Route
          path="/tasks"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resourceKey="nav.tasks">
              <TasksPage onTaskSelected={props.onTaskSelected} bootstrap={props.bootstrap} />
            </Guarded>
          }
        />
        <Route
          path="/evidence"
          element={
            <Guarded roles={ALL_AUTHENTICATED_ROLES} activeRole={activeRole} resourceKey="nav.evidence">
              <EvidencePage taskId={props.activeTaskId ?? ""} locale={props.activeLocale ?? "en"} />
            </Guarded>
          }
        />
        <Route
          path="/people"
          element={
            <Guarded roles={MONITOR_AND_ABOVE} activeRole={activeRole} resourceKey="nav.people">
              {props.bootstrap ? (
                <PeoplePage bootstrap={props.bootstrap} activeRole={activeRole} />
              ) : null}
            </Guarded>
          }
        />
        <Route
          path="/reviews"
          element={
            <Guarded roles={MONITOR_AND_ABOVE} activeRole={activeRole} resourceKey="nav.reviews">
              <ReviewsPage activeRole={activeRole} />
            </Guarded>
          }
        />
        <Route
          path="/admin"
          element={
            <Guarded roles={ADMIN_ONLY} activeRole={activeRole} resourceKey="nav.admin">
              <AIControlPage />
            </Guarded>
          }
        />
        <Route
          path="/agent-access"
          element={
            <Guarded roles={ADMIN_ONLY} activeRole={activeRole} resourceKey="nav.agent_access">
              <AgentAccessPage />
            </Guarded>
          }
        />
        <Route
          path="/operations"
          element={
            <Guarded roles={ADMIN_ONLY} activeRole={activeRole} resourceKey="nav.operations">
              <ExportsPage />
            </Guarded>
          }
        />
        <Route
          path="/dashboard"
          element={
            <Guarded roles={["owner", "monitor"]} activeRole={activeRole} resourceKey="nav.dashboard">
              <DashboardPage />
            </Guarded>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
