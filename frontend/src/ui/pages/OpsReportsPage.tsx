import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  BarChart3,
  Building2,
  CalendarRange,
  ChevronDown,
  Download,
  Filter,
  MoreHorizontal,
  PieChart,
  Sparkles,
  Star,
  Tag,
  TrendingUp,
  Users,
  Wrench,
  type LucideIcon,
} from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsChart, OpsMetric, OpsReportsSnapshot } from '../../domain/models';
import './opsreports.css';

type Tone = 'green' | 'cyan' | 'violet' | 'orange' | 'red';

const tones: Tone[] = ['green', 'cyan', 'violet', 'orange', 'red'];
const metricIcons: LucideIcon[] = [BarChart3, Building2, Tag, Star, Wrench];
const chartIcons: LucideIcon[] = [BarChart3, PieChart, Users, CalendarRange, Sparkles];
const sparklineColor: Record<Tone, string> = {
  green: '#22c55e',
  cyan: '#0ea5e9',
  violet: '#8b5cf6',
  orange: '#f97316',
  red: '#ef4444',
};

function metricSpark(metric: OpsMetric) {
  const seed = [...`${metric.label}${metric.value}`].reduce((total, char) => total + char.charCodeAt(0), 0);
  return Array.from({ length: 12 }, (_, index) => 6 + ((seed + index * 7) % 8));
}

function Sparkline({ vals, color }: { vals: number[]; color: string }) {
  const max = Math.max(...vals, 1);
  const width = 120;
  const height = 28;
  const points = vals.map((value, index) => `${(index / (vals.length - 1)) * width},${height - (value / max) * height * 0.88}`).join(' ');
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="ops-sparkline" aria-hidden="true" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MetricCard({ metric, index }: { metric: OpsMetric; index: number }) {
  const tone = tones[index % tones.length];
  const Icon = metricIcons[index % metricIcons.length];
  return (
    <article className={`ops-kpi ops-kpi--${tone}`}>
      <div className="ops-kpi__head">
        <span className="ops-kpi__icon"><Icon size={17} /></span>
        <p className="ops-kpi__label">{metric.label}</p>
        <button type="button" aria-label={`${metric.label} options`}><MoreHorizontal size={16} /></button>
      </div>
      <strong className="ops-kpi__value">{metric.value}</strong>
      <small className="ops-kpi__delta">{metric.caption}</small>
      <Sparkline vals={metricSpark(metric)} color={sparklineColor[tone]} />
    </article>
  );
}

function ChartBars({ chart, index }: { chart: OpsChart; index: number }) {
  const Icon = chartIcons[index % chartIcons.length];
  return (
    <article className="ops-chart-card ops-rpt-dynamic-card">
      <header>
        <h3><Icon size={16} /> {chart.title}</h3>
        <a href="/ops/reports/">View all</a>
      </header>
      <div className="ops-ch-list">
        {chart.rows.slice(0, 6).map((row) => (
          <div className="ops-ch-row" key={`${chart.id}-${row.label}`}>
            <span className="ops-ch-label" title={row.label}>{row.label}</span>
            <span className="ops-ch-track">
              <i className="ops-ch-fill ops-ch-fill--dynamic" style={{ width: `${row.width}%` }} />
            </span>
            <span className="ops-ch-pct">{row.total}</span>
            <span className="ops-ch-count">{chart.maxTotal ? `${Math.round((row.total / chart.maxTotal) * 100)}%` : '0%'}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function TimelineChart({ chart }: { chart: OpsChart }) {
  const rows = chart.rows.slice(-12);
  const width = 500;
  const height = 185;
  const left = 38;
  const right = 8;
  const top = 12;
  const bottom = 28;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const max = Math.max(...rows.map((row) => row.total), 1);
  const x = (index: number) => left + (index / Math.max(rows.length - 1, 1)) * plotWidth;
  const y = (total: number) => top + (1 - total / max) * plotHeight;
  const path = rows.map((row, index) => `${index === 0 ? 'M' : 'L'}${x(index).toFixed(1)},${y(row.total).toFixed(1)}`).join(' ');
  const area = `${path} L${x(rows.length - 1).toFixed(1)},${top + plotHeight} L${x(0).toFixed(1)},${top + plotHeight} Z`;

  return (
    <article className="ops-chart-card ops-card-rev">
      <header className="ops-card-rev__hdr">
        <div>
          <h3>{chart.title}</h3>
          <div className="ops-rev-legend">
            <span><i className="l-curr" />This period</span>
            <span><i className="l-prev" />Previous period</span>
          </div>
        </div>
        <button type="button" className="ops-daily-btn">Daily <ChevronDown size={13} /></button>
      </header>
      <svg viewBox={`0 0 ${width} ${height}`} className="ops-rev-svg" role="img" aria-label={`${chart.title} trend`}>
        <defs>
          <linearGradient id="ops-rpt-area" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
          <line key={ratio} x1={left} x2={width - right} y1={top + ratio * plotHeight} y2={top + ratio * plotHeight} stroke="#e2e8f0" strokeWidth="0.75" />
        ))}
        <path d={area} fill="url(#ops-rpt-area)" />
        <path d={path} fill="none" stroke="#0ea5e9" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        {rows.map((row, index) => (
          <g key={`${row.label}-${index}`}>
            <circle cx={x(index)} cy={y(row.total)} r="3" fill="#0ea5e9" stroke="#fff" strokeWidth="2" />
            <text x={x(index)} y={height - 5} textAnchor="middle" fontSize="9" fill="#94a3b8" fontFamily="inherit">{row.label.replace('Jun ', 'Jun')}</text>
          </g>
        ))}
      </svg>
    </article>
  );
}

function exportReports(snapshot: OpsReportsSnapshot) {
  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `mladis-reports-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

export function OpsReportsPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsReportsSnapshot | null>(null);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('');

  useEffect(() => {
    let mounted = true;
    service.loadReports()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load reports.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const categories = useMemo(() => {
    if (!snapshot) return [];
    return Array.from(new Set(snapshot.charts.map((chart) => chart.category)));
  }, [snapshot]);

  const visibleCharts = useMemo(() => (
    snapshot ? snapshot.charts.filter((chart) => !category || chart.category === category) : []
  ), [category, snapshot]);

  const timelineChart = visibleCharts.find((chart) => chart.id.includes('timeline')) || visibleCharts[0];
  const sideCharts = visibleCharts.filter((chart) => chart !== timelineChart).slice(0, 2);
  const bottomCharts = visibleCharts.filter((chart) => chart !== timelineChart).slice(2, 5);

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-rpt"><section className="ops-chart-card">Loading reports...</section></main>;
  }

  return (
    <main className="dashboard-content ops-rpt">
      <section className="ops-rpt-hero">
        <div>
          <h2>Reports &amp; Analytics</h2>
          <p className="ops-rpt-hero__subtitle">Measure occupancy, revenue, maintenance costs, booking sources, and operational performance.</p>
        </div>
        <div className="ops-rpt-hero__btns">
          <button className="ops-btn-date" type="button"><CalendarRange size={16} /> {snapshot.reportSince.slice(0, 10)} – {snapshot.reportUntil.slice(0, 10)}</button>
          <button className="ops-btn-sec" type="button" onClick={() => setCategory((current) => (current ? '' : categories[0] || ''))}><Filter size={16} /> Filters</button>
          <button className="ops-btn-sec" type="button" onClick={() => exportReports(snapshot)}><Download size={16} /> Export</button>
        </div>
      </section>

      <section className="ops-rpt-category-row" aria-label="Report categories">
        <button className={!category ? 'is-active' : ''} onClick={() => setCategory('')} type="button">All <small>{snapshot.charts.length}</small></button>
        {categories.map((item) => (
          <button className={category === item ? 'is-active' : ''} key={item} onClick={() => setCategory(item)} type="button">
            {item}
            <small>{snapshot.charts.filter((chart) => chart.category === item).length}</small>
          </button>
        ))}
      </section>

      <section className="ops-kpis">
        {snapshot.summaryCards.slice(0, 5).map((metric, index) => <MetricCard metric={metric} index={index} key={metric.label} />)}
      </section>

      <section className="ops-charts-row">
        {timelineChart && <TimelineChart chart={timelineChart} />}
        {sideCharts.map((chart, index) => <ChartBars chart={chart} index={index} key={chart.id} />)}
      </section>

      <section className="ops-bottom-row">
        {bottomCharts.map((chart, index) => <ChartBars chart={chart} index={index + 2} key={chart.id} />)}
        <article className="ops-chart-card ops-card-insights">
          <header>
            <h3><Sparkles size={16} /> AI Insights</h3>
            <a href="/ops/agent/">Review</a>
          </header>
          <div className="ops-ins-list">
            {visibleCharts.slice(0, 3).map((chart, index) => (
              <article className={`ops-ins-item ops-ins-item--${['green', 'blue', 'orange'][index]}`} key={chart.id}>
                <span><TrendingUp size={15} /></span>
                <div>
                  <strong>{chart.title}</strong>
                  <p>{chart.maxTotal ? `${chart.rows[0]?.label || 'Top record'} leads this report with ${chart.maxTotal} tracked object(s).` : 'No records yet. Keep collecting operational activity.'}</p>
                </div>
              </article>
            ))}
          </div>
          <a href={snapshot.calendarUrl} className="ops-ins-more">Open calendar context</a>
        </article>
      </section>

      <p className="ops-rpt-footnote">All times shown in America/Santo Domingo (AST). Live API snapshot from {snapshot.reportUntil.slice(0, 10)}.</p>
    </main>
  );
}
