/**
 * RouteLoadingScreen — placeholder rendered while a lazy chunk is being
 * fetched. Kept dependency-free so it is safe to ship in the initial bundle.
 */
import { Panel, SkeletonBlock } from "../shell/ui";
import { useTranslation } from "react-i18next";

export function RouteLoadingScreen() {
  const { t } = useTranslation();
  return (
    <div className="route-loading-screen" role="status" aria-live="polite">
      <Panel eyebrow={t("common.loading")} title={t("shell.loading")}>
        <SkeletonBlock rows={3} />
      </Panel>
    </div>
  );
}
