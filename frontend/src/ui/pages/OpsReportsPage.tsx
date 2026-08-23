import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle, BarChart3, Building2, CalendarRange,
  Clock3, Download, Sparkles, Star, Tag, TrendingUp, Link2, Wrench,
} from 'lucide-react';
import { ReportsFactory } from '../../application/ReportsFactory';
import type {
  ReportChannelRow,
  ReportHeatDay,
  ReportInsight,
  ReportListingShare,
  ReportMetric,
  ReportRevenueSeries,
  ReportStayRow,
  ReportWorkspace,
} from '../../domain/reports';
import './opsreports.css';

const REPORT_ICON_COMPONENTS = {
  revenue: BarChart3,
  occupancy: Building2,
  adr: Tag,
  rating: Star,
  maintenance: Wrench,
};

const REPORT_INSIGHT_ICONS = {
  trend: TrendingUp,
  link: Link2,
  warning: AlertTriangle,
};

// ── Helpers ───────────────────────────────────────────────────────────────────

const SPARK_COLORS: Record<string, string> = {
  green: '#22c55e', cyan: '#0ea5e9', violet: '#8b5cf6', orange: '#f97316', red: '#ef4444',
};

function Sparkline({ vals, color }: { vals: number[]; color: string }) {
  if (vals.length < 2) return null;
  const max = Math.max(...vals, 1);
  const W = 120, H = 28;
  const pts = vals
    .map((v, i) => `${(i / (vals.length - 1)) * W},${H - (v / max) * H * 0.88}`)
    .join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="ops-sparkline" aria-hidden="true" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2.2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ── Components ────────────────────────────────────────────────────────────────

function MetricCard({ m }: { m: ReportMetric }) {
  const Icon = REPORT_ICON_COMPONENTS[m.iconKey];
  return (
    <article className={`ops-kpi ops-kpi--${m.tone}`}>
      <div className="ops-kpi__head">
        <span className="ops-kpi__icon"><Icon size={17} /></span>
        <p className="ops-kpi__label">{m.label}</p>
      </div>
      <strong className="ops-kpi__value">{m.value}</strong>
      <small className="ops-kpi__delta">{m.delta}</small>
      <Sparkline vals={m.spark} color={SPARK_COLORS[m.tone]} />
    </article>
  );
}

function RevenueChart({ chart }: { chart: ReportRevenueSeries }) {
  // All coordinates live inside the SVG – zero alignment hacks needed
  const VW = 500, VH = 185;
  const PL = 44, PR = 8, PT = 10, PB = 28;
  const PW = VW - PL - PR;   // 448
  const PH = VH - PT - PB;   // 147
  const observedMax = Math.max(...chart.current, ...chart.previous, 0);
  const MAX_V = Math.max(Math.ceil(observedMax / 5) * 5, 5);
  const N = chart.labels.length;

  const cx = (i: number) => PL + (i / (N - 1)) * PW;
  const cy = (v: number) => PT + (1 - v / MAX_V) * PH;

  const pathFor = (vals: number[]) =>
    vals.map((v, i) => `${i === 0 ? 'M' : 'L'}${cx(i).toFixed(1)},${cy(v).toFixed(1)}`).join(' ');

  const currPath = pathFor(chart.current);
  const prevPath = pathFor(chart.previous);
  const areaPath = `${currPath} L${cx(N - 1).toFixed(1)},${(PT + PH).toFixed(1)} L${cx(0).toFixed(1)},${(PT + PH).toFixed(1)} Z`;

  const yTicks = Array.from({ length: 6 }, (_, index) => (MAX_V / 5) * index);

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
        <span className="ops-daily-btn">Daily</span>
      </header>

      {chart.labels.length ? <svg viewBox={`0 0 ${VW} ${VH}`} className="ops-rev-svg"
           role="img" aria-label={`${chart.title} line chart`}>
        <defs>
          <linearGradient id="rev-area" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%"   stopColor="#0ea5e9" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines + Y-axis labels (inside SVG – guaranteed alignment) */}
        {yTicks.map((v) => (
          <g key={v}>
            <line x1={PL} x2={VW - PR} y1={cy(v)} y2={cy(v)}
                  stroke="#e2e8f0" strokeWidth="0.75" />
            <text x={PL - 5} y={cy(v)} textAnchor="end" dominantBaseline="middle"
                  fontSize="9" fill="#94a3b8" fontFamily="inherit">
              {chart.valuePrefix}{Number.isInteger(v) ? v : v.toFixed(1)}{chart.valueSuffix}
            </text>
          </g>
        ))}

        {/* Area fill */}
        <path d={areaPath} fill="url(#rev-area)" />

        {/* Previous period – dashed gray */}
        <path d={prevPath} fill="none" stroke="#cbd5e1" strokeWidth="1.8"
              strokeDasharray="5,4" strokeLinecap="round" strokeLinejoin="round" />

        {/* Current period – solid blue */}
        <path d={currPath} fill="none" stroke="#0ea5e9" strokeWidth="2.4"
              strokeLinecap="round" strokeLinejoin="round" />

        {/* Dots on current period */}
        {chart.current.map((v, i) => (
          <circle key={i} cx={cx(i)} cy={cy(v)} r="3" fill="#0ea5e9" stroke="#fff" strokeWidth="2" />
        ))}

        {/* X-axis labels (inside SVG = guaranteed alignment with data points) */}
        {chart.labels.map((lbl, i) => (
          <text key={lbl} x={cx(i)} y={VH - 5} textAnchor="middle"
                fontSize="9" fill="#94a3b8" fontFamily="inherit">
            {lbl}
          </text>
        ))}
      </svg> : <p>No reservation requests were recorded for this report period.</p>}
    </article>
  );
}

function ChannelsCard({ channels, title }: { channels: ReportChannelRow[]; title: string }) {
  return (
    <article className="ops-chart-card ops-card-ch">
      <header>
        <h3>{title}</h3>
      </header>
      <div className="ops-ch-list">
        {channels.map((row) => (
          <div key={row.label} className="ops-ch-row">
            <span className="ops-ch-label">{row.label}</span>
            <div className="ops-ch-track">
              <div className="ops-ch-fill" style={{ width: `${row.pct}%` }} />
            </div>
            <b className="ops-ch-pct">{row.pct}%</b>
            <span className="ops-ch-count">{row.bookings} bkg</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function DonutCard({
  listings, note, title, totalLabel,
}: {
  listings: ReportListingShare[];
  note: string;
  title: string;
  totalLabel: string;
}) {
  let cursor = 0;
  const stops = listings.map((listing) => {
    const start = cursor;
    cursor += listing.pct;
    return `${listing.color} ${start}% ${cursor}%`;
  });
  const donutBackground = stops.length ? `conic-gradient(${stops.join(', ')})` : '#e2e8f0';
  return (
    <article className="ops-chart-card ops-card-donut">
      <header>
        <h3>{title}</h3>
      </header>
      <div className="ops-donut-body">
        <div className="ops-donut ops-donut--mix" style={{ background: donutBackground }}>
          <div className="ops-donut__inner">
            <strong>{totalLabel}</strong>
            <span>Total</span>
          </div>
        </div>
        <ul className="ops-dl">
          {listings.map((l) => (
            <li key={l.label}>
              <i className={l.toneClass} />
              <span className="odl-name">{l.label}</span>
              <b className="odl-pct">{l.pct}%</b>
              <span className="odl-amt">{l.amount}</span>
            </li>
          ))}
        </ul>
      </div>
      <p className="ops-donut-note">{note}</p>
    </article>
  );
}

function HeatmapCard({
  heatDays, periodLabel, title,
}: {
  heatDays: ReportHeatDay[];
  periodLabel: string;
  title: string;
}) {
  return (
    <article className="ops-chart-card ops-card-heat">
      <header>
        <h3>{title}</h3>
        <div className="ops-hm-ctrl">
          <span className="ops-hm-month">{periodLabel}</span>
        </div>
      </header>
      <div className="ops-hm-grid">
        {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map((d) => <span key={d}>{d}</span>)}
        {heatDays.map((cell, idx) => (
          <span key={idx} className={`ops-hm-cell ops-hm-cell--${cell.intensity}`}>
            {cell.day || ''}
          </span>
        ))}
      </div>
      <div className="ops-hm-legend">
        <span>0%</span>
        <div className="ops-hm-scale">
          {[0,1,2,3,4,5].map((i) => <i key={i} className={`hms-${i}`} />)}
        </div>
        <span>100%</span>
      </div>
      <p className="ops-hm-tz">All times shown in America/Santo Domingo (AST)</p>
    </article>
  );
}

function StaysCard({
  columnLabels, countLabel, stays, title,
}: {
  columnLabels: readonly [string, string, string, string, string, string];
  countLabel: string;
  stays: ReportStayRow[];
  title: string;
}) {
  return (
    <article className="ops-chart-card ops-card-stays">
      <header>
        <h3>{title}</h3>
      </header>
      <div className="ops-stays-scroll">
        <table className="ops-stays">
          <colgroup>
            <col className="ops-stays-col-listing" />
            <col className="ops-stays-col-revenue" />
            <col className="ops-stays-col-occupancy" />
            <col className="ops-stays-col-adr" />
            <col className="ops-stays-col-rating" />
            <col className="ops-stays-col-trend" />
          </colgroup>
          <thead>
            <tr>
              {columnLabels.map((label) => <th key={label}>{label}</th>)}
            </tr>
          </thead>
          <tbody>
            {stays.map((s) => (
              <tr key={s.listing}>
                <td>
                  <div className="ops-stay-cell">
                    {s.imgSrc
                      ? <img src={s.imgSrc} className="ops-thumb" alt="" referrerPolicy="no-referrer" />
                      : <span className={`ops-thumb ${s.toneClass}`} aria-hidden="true" />}
                    <div className="ops-stay-info">
                      <strong>{s.listing}</strong>
                      <small>{s.sub}</small>
                    </div>
                  </div>
                </td>
                <td>{s.revenue}</td>
                <td>{s.occ}</td>
                <td>{s.adr}</td>
                <td>{s.rating}</td>
                <td><span className={s.delta === '-' ? 'td-flat' : s.delta.startsWith('-') ? 'td-down' : 'td-up'}>{s.delta}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="ops-stays-foot">
          <span>{countLabel}</span>
      </div>
    </article>
  );
}

function InsightsCard({ insights, title }: { insights: ReportInsight[]; title: string }) {
  return (
    <article className="ops-chart-card ops-card-insights">
      <header>
        <h3><Sparkles size={17} />{title}</h3>
      </header>
      <div className="ops-ins-list">
        {insights.map(({ title, body, tone, iconKey }) => {
          const Icon = REPORT_INSIGHT_ICONS[iconKey];
          return (
          <div key={title} className={`ops-ins ops-ins--${tone}`}>
            <span className="ops-ins__ico"><Icon size={14} /></span>
            <div>
              <strong>{title}</strong>
              <p>{body}</p>
            </div>
          </div>
          );
        })}
      </div>
      <div className="ops-ins-foot">
        <Clock3 size={12} /><span>Derived from the current reports API snapshot</span>
      </div>
    </article>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function OpsReportsPage() {
  const service = useMemo(() => ReportsFactory.create(), []);
  const [workspace, setWorkspace] = useState<ReportWorkspace>(() => service.fallbackWorkspace());

  useEffect(() => {
    let active = true;
    service.loadWorkspace()
      .then((nextWorkspace) => {
        if (active) setWorkspace(nextWorkspace);
      })
      .catch(() => {
        if (active) setWorkspace(service.fallbackWorkspace());
      });
    return () => {
      active = false;
    };
  }, [service]);

  return (
    <main className="dashboard-content ops-page ops-rpt">

      {/* ── Hero ── */}
      <div className="ops-rpt-hero">
        <div>
          <h2>Reports &amp; Analytics</h2>
          <p className="ops-rpt-hero__subtitle">{workspace.heroSubtitle}</p>
        </div>
        <div className="ops-rpt-hero__btns">
          <span className="ops-btn-date">
            <CalendarRange size={15} />{workspace.dateRangeLabel}
          </span>
          <a className="ops-btn-sec" href="/api/ops/reports/" download="mladis-operational-report.json">
            <Download size={14} />Export
          </a>
        </div>
      </div>

      {/* ── KPI row ── */}
      <div className="ops-kpis" aria-label="Summary metrics">
        {workspace.metrics.map((m) => <MetricCard key={m.label} m={m} />)}
      </div>

      {/* ── Charts row ── */}
      <div className="ops-charts-row">
        <RevenueChart chart={workspace.revenueSeries} />
        <ChannelsCard channels={workspace.channels} title={workspace.channelTitle} />
        <DonutCard listings={workspace.listings} note={workspace.listingNote} title={workspace.listingTitle} totalLabel={workspace.listingTotalLabel} />
      </div>

      {/* ── Bottom row ── */}
      <div className="ops-bottom-row">
        <HeatmapCard heatDays={workspace.heatDays} periodLabel={workspace.heatmapPeriodLabel} title={workspace.heatmapTitle} />
        <StaysCard columnLabels={workspace.stayColumnLabels} countLabel={workspace.staysCountLabel} stays={workspace.stays} title={workspace.staysTitle} />
        <InsightsCard insights={workspace.insights} title={workspace.insightsTitle} />
      </div>

    </main>
  );
}
