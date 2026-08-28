/**
 * AsyncState — composable loading / error / empty surface used by every
 * workspace page. Keeping the surface in one place ensures all panels
 * honour the same accessibility contract (aria-live, focus management).
 */
import type { ReactNode } from "react";

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
  emptyMessage = "Nothing to display yet.",
  loadingLabel = "Loading…",
  children,
}: AsyncStateProps) {
  if (error) {
    return (
      <div className="async-state async-state-error" role="alert">
        <strong>Something went wrong</strong>
        <p>{error}</p>
      </div>
    );
  }
  if (loading) {
    return (
      <div className="async-state async-state-loading" role="status" aria-live="polite">
        <span className="async-state-spinner" aria-hidden="true" />
        <span>{loadingLabel}</span>
      </div>
    );
  }
  if (empty) {
    return (
      <div className="async-state async-state-empty" role="status">
        <p>{emptyMessage}</p>
      </div>
    );
  }
  return <>{children}</>;
}
