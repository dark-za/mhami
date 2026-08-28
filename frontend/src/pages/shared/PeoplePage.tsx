/** PeoplePage — read-only view of the bootstrap user/company/branches. */

import { Panel } from "../../shell/ui";
import type { BootstrapState } from "../../api/bootstrap";
import { roleLabels } from "../../design-system/tokens";

export interface PeoplePageProps {
  bootstrap: BootstrapState;
  activeRole: BootstrapState["snapshot"]["currentUser"]["role"];
}

export function PeoplePage({ bootstrap, activeRole }: PeoplePageProps) {
  const { company, currentUser } = bootstrap.snapshot;
  return (
    <Panel eyebrow="People" title="Company and active members">
      <div className="token-grid">
        <div className="token-swatch">
          <span>Company</span>
          <strong>{company.name}</strong>
        </div>
        <div className="token-swatch">
          <span>Code</span>
          <strong>{company.code}</strong>
        </div>
        <div className="token-swatch">
          <span>Status</span>
          <strong>{company.status}</strong>
        </div>
      </div>
      <p className="muted">
        Active session: <strong>{currentUser.displayName}</strong> ({currentUser.loginId}) ·{" "}
        {roleLabels[activeRole].en}
      </p>
      <p className="muted">
        Branches available in the live snapshot: {bootstrap.branches.length}. Use the Reviews page
        for ownership and policy actions.
      </p>
    </Panel>
  );
}
