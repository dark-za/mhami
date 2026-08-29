/** Small UI primitives shared by every workspace panel. */

import type { ReactNode } from "react";

export function Badge({ tone, children }: { tone: string; children: string }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Panel({
  title,
  eyebrow,
  children,
  variant = "section",
}: {
  title: string;
  eyebrow: string;
  children: ReactNode;
  variant?: "section" | "action" | "insight";
}) {
  return (
    <section className={`panel panel-${variant}`}>
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function StateCard({
  title,
  body,
  tone,
}: {
  title: string;
  body: string;
  tone: string;
}) {
  return (
    <article className={`state-card state-${tone}`}>
      <strong>{title}</strong>
      <p>{body}</p>
    </article>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty-state" role="status">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}

export function SkeletonBlock({ rows = 3 }: { rows?: number }) {
  return (
    <div className="skeleton-stack" aria-label="Loading">
      {Array.from({ length: rows }).map((_, index) => (
        <span key={index} className="skeleton-line" />
      ))}
    </div>
  );
}
