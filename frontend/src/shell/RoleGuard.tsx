/** RoleGuard — render the child route only when the active role is permitted.

Renders a friendly notice when access is denied rather than a blank screen so
the shell never looks broken in a preview build.
*/

import type { ReactNode } from "react";

import type { Role } from "../design-system/tokens";
import { Panel } from "./ui";

export interface RoleGuardProps {
  roles: Role[];
  activeRole: Role | null;
  children: ReactNode;
  resource?: string;
}

export function RoleGuard({ roles, activeRole, children, resource }: RoleGuardProps) {
  if (activeRole && roles.includes(activeRole)) {
    return <>{children}</>;
  }
  return (
    <Panel eyebrow="Access restricted" title={resource ?? "You do not have access to this page"}>
      <p className="muted">
        This page is reserved for the following roles: {roles.join(", ")}. The shell will surface it
        once the authenticated session is upgraded.
      </p>
    </Panel>
  );
}
