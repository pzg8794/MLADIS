import { useEffect, useMemo, useState } from 'react';
import { BarChart3, CalendarRange, Database, Download } from 'lucide-react';
import { ReportsFactory } from '../../application/ReportsFactory';
import type { ReportChart, ReportMetric, ReportWorkspace } from '../../domain/reports';
import './opsreports.css';

function MetricCard({ metric }: { metric: ReportMetric }) {
  return (
    <article className={`ops-kpi ops-kpi--${metric.tone}`}>
      <div className="ops-kpi__head">
        <span className="ops-kpi__icon"><Database size={17} /></span>
        <p className="ops-kpi__label">{metric.label}</p>
      </div>
      <strong className="ops-kpi__value">{metric.value}</strong>
      <small className="ops-kpi__delta">{metric.caption}</small>
    </article>
  );
}

function ChartCard({ chart }: { chart: ReportChart }) {
  const maxTotal = Math.max(...chart.rows.map((row) => row.total), 1);
  return (
    <article className="ops-chart-card ops-live-report-card">
      <header>
        <div><h3>{chart.title}</h3><small>{chart.category}</small></div>
      </header>
      {chart.rows.length ? (
        <div className="ops-live-report-rows">
          {chart.rows.map((row) => (
            <div className="ops-live-report-row" key={row.label}>
              <span title={row.label}>{row.label}</span>
              <div><i style={{ width: `${Math.max((row.total / maxTotal) * 100, row.total ? 4 : 0)}%` }} /></div>
              <strong>{row.total}</strong>
            </div>
          ))}
        </div>
      ) : <p className="ops-live-report-empty">No matching records in this reporting period.</p>}
    </article>
  );
}

export function OpsReportsPage() {
  const service = useMemo(() => ReportsFactory.create(), []);
  const [workspace, setWorkspace] = useState<ReportWorkspace>(() => service.fallbackWorkspace());

  useEffect(() => {
    let active = true;
    service.loadWorkspace().then((next) => { if (active) setWorkspace(next); });
    return () => { active = false; };
  }, [service]);

  return (
    <main className="dashboard-content ops-page ops-rpt">
      <div className="ops-rpt-hero">
        <div>
          <h2>Reports &amp; Analytics</h2>
          <p className="ops-rpt-hero__subtitle">Live reservations, guests, inventory, traffic, deposits, and campaign reporting.</p>
        </div>
        <div className="ops-rpt-hero__btns">
          <span className="ops-btn-date"><CalendarRange size={15} />{workspace.dateRangeLabel}</span>
          <a className="ops-btn-sec" href="/api/ops/reports/" download="mladis-operational-report.json"><Download size={14} />Export JSON</a>
        </div>
      </div>
      {workspace.metrics.length ? (
        <div className="ops-kpis ops-kpis--live" aria-label="Live summary metrics">
          {workspace.metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
        </div>
      ) : (
        <section className="ops-live-report-status"><Database size={20} /><p>Live report data is temporarily unavailable.</p></section>
      )}
      <div className="ops-live-report-grid">
        {workspace.visibleCharts().map((chart) => <ChartCard chart={chart} key={chart.id} />)}
      </div>
      <footer className="ops-live-report-footer">
        <BarChart3 size={14} /><span>{workspace.generatedAtLabel}</span><span>Source: {workspace.source === 'api' ? 'live database records' : 'unavailable'}</span>
      </footer>
    </main>
  );
}
