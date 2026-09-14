/** DashboardPage - owner/monitor dashboard showing company summary and branches. */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import type { ReviewDashboard } from "../domain";
import { Panel, SkeletonBlock } from "../shell/ui";

export function DashboardPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<ReviewDashboard | null>(null);
  const [period, setPeriod] = useState("day");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    void api<ReviewDashboard>(`/api/v1/reviews/dashboard?period=${period}`)
      .then((payload) => {
        if (active) {
          setData(payload);
        }
      })
      .catch((_error: unknown) => {
        if (active) {
          setError(t("errors.generic"));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [period]);

  if (loading) {
    return (
      <Panel eyebrow={t("dashboard.eyebrow")} title={t("dashboard.overview")}>
        <SkeletonBlock rows={5} />
      </Panel>
    );
  }

  if (error) {
    return (
      <Panel eyebrow={t("dashboard.eyebrow")} title={t("dashboard.overview")}>
        <p className="status status-danger">{error}</p>
      </Panel>
    );
  }

  if (!data) {
    return (
      <Panel eyebrow={t("dashboard.eyebrow")} title={t("dashboard.overview")}>
        <p className="muted">{t("dashboard.no_data")}</p>
      </Panel>
    );
  }

  return (
    <Panel eyebrow={t("dashboard.eyebrow")} title={t("dashboard.overview")}>
      <div className="dashboard-toolbar">
        <div>
          <p className="muted">{data.company.name ?? t("dashboard.company")}</p>
          <p className="dashboard-caption">{t("dashboard.summary")}</p>
        </div>
        <div className="chip-row" aria-label={t("dashboard.selected_period")}>
          {[
            ["day", t("dashboard.today")],
            ["three_days", t("dashboard.three_days")],
            ["week", t("dashboard.week")],
            ["month", t("dashboard.month")],
          ].map(([value, label]) => (
            <button key={value} className={`chip ${period === value ? "chip-active" : ""}`} type="button" aria-pressed={period === value} onClick={() => setPeriod(value)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <section className="dashboard-metrics" aria-label={t("dashboard.task_team_summary")}>
        <article className="metric-card metric-card-positive"><span>{t("dashboard.completed_today")}</span><strong>{data.summary.completed_today ?? 0}</strong><small>{t("dashboard.tasks_closed_today")}</small></article>
        <article className="metric-card metric-card-danger"><span>{t("dashboard.overdue")}</span><strong>{data.summary.overdue ?? 0}</strong><small>{t("dashboard.need_attention")}</small></article>
        <article className="metric-card metric-card-warning"><span>{t("dashboard.quality_exceptions")}</span><strong>{data.summary.quality_exceptions ?? 0}</strong><small>{t("dashboard.open_review_items")}</small></article>
        <article className="metric-card"><span>{t("dashboard.pending")}</span><strong>{data.summary.pending ?? 0}</strong><small>{t("dashboard.waiting_to_start")}</small></article>
        <article className="metric-card"><span>{t("dashboard.in_progress")}</span><strong>{data.summary.in_progress ?? 0}</strong><small>{t("dashboard.currently_handled")}</small></article>
        <article className="metric-card"><span>{t("dashboard.cancelled")}</span><strong>{data.summary.cancelled ?? 0}</strong><small>{t("dashboard.selected_period")}</small></article>
      </section>

      <div className="dashboard-detail-grid">
        <section className="dashboard-section" aria-labelledby="trend-heading">
          <div className="section-heading">
            <div><p className="eyebrow">{t("dashboard.performance")}</p><h3 id="trend-heading">{t("dashboard.completion_trend")}</h3></div>
            <strong>{data.summary.completed_in_period ?? 0}<small> {t("dashboard.completed")}</small></strong>
          </div>
          <div className="metric-strip" aria-label={t("dashboard.completion_trend")}>
            {data.trend.map((point) => {
              const maximum = Math.max(1, ...data.trend.map((item) => item.completed));
              const width = `${Math.max(8, Math.round((point.completed / maximum) * 100))}%`;
              return <div key={point.date} className="metric-row"><span>{point.date}</span><div className="metric-track"><span className="metric-bar" style={{ width }} /></div><strong>{point.completed}</strong></div>;
            })}
          </div>
        </section>
        <section className="dashboard-section" aria-labelledby="team-heading">
          <div className="section-heading"><div><p className="eyebrow">{t("dashboard.capacity")}</p><h3 id="team-heading">{t("dashboard.team_coverage")}</h3></div></div>
          <dl className="capacity-list">
            <div><dt>{t("dashboard.employees")}</dt><dd>{data.summary.employees ?? 0}</dd></div>
            <div><dt>{t("dashboard.monitors")}</dt><dd>{data.summary.monitors ?? 0}</dd></div>
            <div><dt>{t("dashboard.branches")}</dt><dd>{data.summary.branches ?? 0}</dd></div>
          </dl>
        </section>
      </div>

      <section className="dashboard-section" aria-labelledby="branches-heading">
        <div className="section-heading"><div><p className="eyebrow">{t("dashboard.coverage")}</p><h3 id="branches-heading">{t("dashboard.branches")}</h3></div></div>
        <div className="branch-list" role="list">
          {data.branches.map((branch) => (
            <article key={branch.branch_id} className="branch-row" role="listitem">
              <strong>{branch.branch_name}</strong>
              <span><b>{branch.completed_today}</b> {t("dashboard.completed")}</span>
              <span><b>{branch.pending}</b> {t("dashboard.pending")}</span>
              <span><b>{branch.overdue}</b> {t("dashboard.overdue")}</span>
              <span><b>{branch.quality_exceptions}</b> {t("dashboard.exceptions")}</span>
            </article>
          ))}
        </div>
      </section>
    </Panel>
  );
}

export default DashboardPage;
