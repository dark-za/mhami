/** Small UI primitives shared by every workspace panel. */

import type { ReactNode } from "react";

export function Badge({ tone, children }: { tone: string; children: string }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Panel({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: ReactNode;
}) {
  return (
    <section className="panel">
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
