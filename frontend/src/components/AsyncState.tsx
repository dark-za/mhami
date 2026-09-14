/**
 * AsyncState — composable loading / error / empty surface used by every
 * workspace page. Keeping the surface in one place ensures all panels
 * honour the same accessibility contract (aria-live, focus management).
 */
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

export interface AsyncStateProps {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
  children: ReactNode;
  loadingLabel?: string;
}

export function AsyncState({
  loading,
  error,
  empty,
  emptyMessage,
  loadingLabel,
  children,
}: AsyncStateProps) {
  const { t } = useTranslation();
  if (error) {
    return (
      <div className="async-state async-state-error" role="alert">
        <strong>{t("async.error_title")}</strong>
        <p>{error}</p>
      </div>
    );
  }
  if (loading) {
    return (
      <div className="async-state async-state-loading" role="status" aria-live="polite">
        <span className="async-state-spinner" aria-hidden="true" />
        <span>{loadingLabel ?? t("async.loading")}</span>
      </div>
    );
  }
  if (empty) {
    return (
      <div className="async-state async-state-empty" role="status">
        <p>{emptyMessage ?? t("async.empty")}</p>
      </div>
    );
  }
  return <>{children}</>;
}
