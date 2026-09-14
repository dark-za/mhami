/** RoleGuard — render the child route only when the active role is permitted.

Renders a friendly notice when access is denied rather than a blank screen so
the shell never looks broken in a preview build.
*/

import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { Role } from "../design-system/tokens";
import { Panel } from "./ui";

export interface RoleGuardProps {
  roles: Role[];
  activeRole: Role | null;
  children: ReactNode;
  resourceKey?: string;
}

export function RoleGuard({ roles, activeRole, children, resourceKey }: RoleGuardProps) {
  const { t } = useTranslation();
  if (activeRole && roles.includes(activeRole)) {
    return <>{children}</>;
  }
  return (
    <Panel eyebrow={t("shell.access_restricted")} title={resourceKey ? t(resourceKey) : t("shell.no_access")}>
      <p className="muted">{t("shell.access_explainer", {
        roles: roles.map((role) => t(`people.role.${role}`)).join("، "),
      })}</p>
    </Panel>
  );
}
