/**
 * RouteLoadingScreen — placeholder rendered while a lazy chunk is being
 * fetched. Kept dependency-free so it is safe to ship in the initial bundle.
 */
import { Panel } from "../shell/ui";

export function RouteLoadingScreen() {
  return (
    <div className="route-loading-screen" role="status" aria-live="polite">
      <Panel eyebrow="Loading" title="Preparing the workspace…">
        <p className="muted">A workspace route is being loaded.</p>
      </Panel>
    </div>
  );
}
