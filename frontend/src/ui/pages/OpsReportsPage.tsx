import {
  AlertTriangle, BarChart3, Building2, CalendarRange, ChevronDown, ChevronLeft, ChevronRight,
  Clock3, Download, Filter,
  MoreHorizontal, Sparkles, Star, Tag, TrendingUp, Link2, Users, Wrench,
} from 'lucide-react';
import './opsreports.css';

// ── Types ────────────────────────────────────────────────────────────────────

type Tone = 'green' | 'cyan' | 'violet' | 'orange' | 'red';

type Metric = {
  label: string;
  value: string;
  delta: string;
  icon: typeof BarChart3;
  tone: Tone;
  spark: number[];
};

type ChannelRow = { label: string; pct: number; bookings: number; widthClass: string };

type ListingShare = {
  label: string;
  pct: number;
  amount: string;
  toneClass: string;
};

type HeatDay = { day: number; intensity: number };

type Insight = {
  title: string;
  body: string;
  tone: 'green' | 'blue' | 'orange';
  Icon: typeof Sparkles;
};

type StayRow = {
  listing: string;
  sub: string;
  revenue: string;
  occ: string;
  adr: string;
  rating: string;
  delta: string;
  tc: string;
  imgSrc: string;
};

// ── Data ─────────────────────────────────────────────────────────────────────

const metrics: Metric[] = [
  { label: 'Revenue',               value: '$18,540',  delta: '+15% vs Jun 29 – Jul 5',  icon: BarChart3,  tone: 'green',  spark: [9,10,9,11,10,12,13,11,12,13,12,14] },
  { label: 'Occupancy',             value: '72%',      delta: '+5pp vs Jun 29 – Jul 5',   icon: Building2, tone: 'cyan',   spark: [7,8,8,9,10,9,8,7,8,9,8,8] },
  { label: 'ADR (Avg. Daily Rate)', value: '$132',     delta: '+7% vs Jun 29 – Jul 5',   icon: Tag,       tone: 'violet', spark: [8,9,8,9,8,10,11,10,9,10,9,10] },
  { label: 'Guest Rating',          value: '4.93 / 5', delta: '+0.05 vs Jun 29 – Jul 5', icon: Star,      tone: 'orange', spark: [9,9,10,9,10,10,9,10,9,10,9,10] },
  { label: 'Maintenance Cost',      value: '$2,310',   delta: '–6% vs Jun 29 – Jul 5',   icon: Wrench,    tone: 'red',    spark: [7,8,8,7,8,7,8,8,7,8,7,7] },
];

// 7 data points – one per day (Jun 6–12), values in $K
const chart = {
  curr:   [8, 11, 14.5, 13, 16, 18, 18.5],
  prev:   [5,  7,    8,  9, 10, 11,   14],
  labels: ['Jun 6','Jun 7','Jun 8','Jun 9','Jun 10','Jun 11','Jun 12'],
};

const channels: ChannelRow[] = [
  { label: 'Direct Website', pct: 42, bookings: 26, widthClass: 'is-42' },
  { label: 'Airbnb',         pct: 28, bookings: 17, widthClass: 'is-28' },
  { label: 'Booking.com',    pct: 16, bookings: 10, widthClass: 'is-16' },
  { label: 'Vrbo',           pct:  8, bookings:  5, widthClass: 'is-8' },
  { label: 'Other',          pct:  6, bookings:  4, widthClass: 'is-6' },
];

const listings: ListingShare[] = [
  { label: '6 Beds Apt, Vacation Home & Pool, G-101', pct: 34, amount: '$6,304', toneClass: 'is-blue' },
  { label: '2 Beds Apt, Vacation Home & Pool',         pct: 26, amount: '$4,816', toneClass: 'is-violet' },
  { label: '3 Beds Apt, Vacation Home & Pool, G-101',  pct: 20, amount: '$3,708', toneClass: 'is-orange' },
  { label: 'Meeting Room 1',                           pct:  8, amount: '$1,482', toneClass: 'is-red' },
  { label: 'Others',                                   pct: 12, amount: '$2,230', toneClass: 'is-gray' },
];

const heatDays: HeatDay[] = [
  { day: 31, intensity: 0 }, { day:  1, intensity: 1 }, { day:  2, intensity: 2 },
  { day:  3, intensity: 3 }, { day:  4, intensity: 3 }, { day:  5, intensity: 4 },
  { day:  6, intensity: 5 }, { day:  7, intensity: 1 }, { day:  8, intensity: 2 },
  { day:  9, intensity: 3 }, { day: 10, intensity: 4 }, { day: 11, intensity: 4 },
  { day: 12, intensity: 5 }, { day: 13, intensity: 5 }, { day: 14, intensity: 2 },
  { day: 15, intensity: 2 }, { day: 16, intensity: 3 }, { day: 17, intensity: 4 },
  { day: 18, intensity: 4 }, { day: 19, intensity: 5 }, { day: 20, intensity: 5 },
  { day: 21, intensity: 2 }, { day: 22, intensity: 2 }, { day: 23, intensity: 3 },
  { day: 24, intensity: 4 }, { day: 25, intensity: 4 }, { day: 26, intensity: 5 },
  { day: 27, intensity: 5 }, { day: 28, intensity: 2 }, { day: 29, intensity: 1 },
  { day: 30, intensity: 1 }, { day:  1, intensity: 0 },
];

const insights: Insight[] = [
  { title: 'Revenue is up 15%',           body: 'You earned $18,540 this week, up 15% compared to Jun 29 – Jul 5.',                                  tone: 'green',  Icon: TrendingUp    },
  { title: 'Direct bookings are growing', body: 'Direct website bookings increased 12% and now represent 42% of total bookings.',                     tone: 'blue',   Icon: Link2         },
  { title: 'Occupancy dips on weekdays',  body: 'Tuesday and Wednesday show the lowest occupancy (58%). Consider promotions to boost midweek demand.', tone: 'orange', Icon: AlertTriangle  },
];

const BASE = import.meta.env.BASE_URL;
const stays: StayRow[] = [
  { listing: '6 Beds Apt, Vacation Home & Pool, G-101', sub: 'Apt #16 · 5 beds',      revenue: '$6,304', occ: '78%', adr: '$146', rating: '4.97', delta: '+2', tc: 'tc-blue',   imgSrc: `${BASE}stays/stay-6br.jpg` },
  { listing: '2 Beds Apt, Vacation Home & Pool',         sub: 'Apt #7 · 2 beds',        revenue: '$4,816', occ: '71%', adr: '$128', rating: '4.92', delta: '—',  tc: 'tc-violet', imgSrc: `${BASE}stays/stay-2br.jpg` },
  { listing: '3 Beds Apt, Vacation Home & Pool, G-101',  sub: 'Apt #13 · 3 beds',       revenue: '$3,708', occ: '69%', adr: '$116', rating: '4.90', delta: '+1', tc: 'tc-orange', imgSrc: `${BASE}stays/stay-3br.jpg` },
  { listing: 'Meeting Room 1',                           sub: 'Conference space',        revenue: '$1,482', occ: '62%', adr: '$89',  rating: '4.85', delta: '+1', tc: 'tc-red',    imgSrc: `${BASE}stays/stay-3br.jpg` },
  { listing: 'Conference Room A',                        sub: 'Meeting room · seats 8',  revenue: '$1,205', occ: '58%', adr: '$76',  rating: '4.70', delta: '+1', tc: 'tc-slate',  imgSrc: `${BASE}stays/stay-2br.jpg` },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

const SPARK_COLORS: Record<string, string> = {
  green: '#22c55e', cyan: '#0ea5e9', violet: '#8b5cf6', orange: '#f97316', red: '#ef4444',
};

function Sparkline({ vals, color }: { vals: number[]; color: string }) {
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

function MetricCard({ m }: { m: Metric }) {
  const Icon = m.icon;
  return (
    <article className={`ops-kpi ops-kpi--${m.tone}`}>
      <div className="ops-kpi__head">
        <span className="ops-kpi__icon"><Icon size={17} /></span>
        <p className="ops-kpi__label">{m.label}</p>
        <button type="button" aria-label={`${m.label} options`}><MoreHorizontal size={16} /></button>
      </div>
      <strong className="ops-kpi__value">{m.value}</strong>
      <small className="ops-kpi__delta">{m.delta}</small>
      <Sparkline vals={m.spark} color={SPARK_COLORS[m.tone]} />
    </article>
  );
}

function RevenueChart() {
  // All coordinates live inside the SVG – zero alignment hacks needed
  const VW = 500, VH = 185;
  const PL = 44, PR = 8, PT = 10, PB = 28;
  const PW = VW - PL - PR;   // 448
  const PH = VH - PT - PB;   // 147
  const MAX_V = 25;
  const N = chart.labels.length; // 7

  const cx = (i: number) => PL + (i / (N - 1)) * PW;
  const cy = (v: number) => PT + (1 - v / MAX_V) * PH;

  const pathFor = (vals: number[]) =>
    vals.map((v, i) => `${i === 0 ? 'M' : 'L'}${cx(i).toFixed(1)},${cy(v).toFixed(1)}`).join(' ');

  const currPath = pathFor(chart.curr);
  const prevPath = pathFor(chart.prev);
  const areaPath = `${currPath} L${cx(N - 1).toFixed(1)},${(PT + PH).toFixed(1)} L${cx(0).toFixed(1)},${(PT + PH).toFixed(1)} Z`;

  const yTicks = [0, 5, 10, 15, 20, 25];

  return (
    <article className="ops-chart-card ops-card-rev">
      <header className="ops-card-rev__hdr">
        <div>
          <h3>Revenue Over Time</h3>
          <div className="ops-rev-legend">
            <span><i className="l-curr" />This period</span>
            <span><i className="l-prev" />Previous period</span>
          </div>
        </div>
        <button type="button" className="ops-daily-btn">Daily <ChevronDown size={13} /></button>
      </header>

      <svg viewBox={`0 0 ${VW} ${VH}`} className="ops-rev-svg"
           role="img" aria-label="Revenue over time line chart">
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
              ${v}K
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
        {chart.curr.map((v, i) => (
          <circle key={i} cx={cx(i)} cy={cy(v)} r="3" fill="#0ea5e9" stroke="#fff" strokeWidth="2" />
        ))}

        {/* X-axis labels (inside SVG = guaranteed alignment with data points) */}
        {chart.labels.map((lbl, i) => (
          <text key={lbl} x={cx(i)} y={VH - 5} textAnchor="middle"
                fontSize="9" fill="#94a3b8" fontFamily="inherit">
            {lbl}
          </text>
        ))}
      </svg>
    </article>
  );
}

function ChannelsCard() {
  return (
    <article className="ops-chart-card ops-card-ch">
      <header>
        <h3>Bookings by Channel</h3>
        <a href="/ops/reports/">View all</a>
      </header>
      <div className="ops-ch-list">
        {channels.map((row) => (
          <div key={row.label} className="ops-ch-row">
            <span className="ops-ch-label">{row.label}</span>
            <div className="ops-ch-track">
              <div className={`ops-ch-fill ${row.widthClass}`} />
            </div>
            <b className="ops-ch-pct">{row.pct}%</b>
            <span className="ops-ch-count">{row.bookings} bkg</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function DonutCard() {
  return (
    <article className="ops-chart-card ops-card-donut">
      <header>
        <h3>Revenue Mix by Listing</h3>
        <a href="/ops/reports/">View all</a>
      </header>
      <div className="ops-donut-body">
        <div className="ops-donut ops-donut--mix">
          <div className="ops-donut__inner">
            <strong>$18,540</strong>
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
      <p className="ops-donut-note">Based on paid revenue</p>
    </article>
  );
}

function HeatmapCard() {
  return (
    <article className="ops-chart-card ops-card-heat">
      <header>
        <h3>Occupancy Heatmap</h3>
        <div className="ops-hm-ctrl">
          <span className="ops-hm-month">June 2026</span>
          <div className="ops-hm-nav">
            <button type="button" aria-label="Previous month"><ChevronLeft size={13} /></button>
            <button type="button" aria-label="Next month"><ChevronRight size={13} /></button>
          </div>
        </div>
      </header>
      <div className="ops-hm-grid">
        {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map((d) => <span key={d}>{d}</span>)}
        {heatDays.map((cell, idx) => (
          <button key={idx} type="button" className={`ops-hm-cell ops-hm-cell--${cell.intensity}`}>
            {cell.day}
          </button>
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

function StaysCard() {
  return (
    <article className="ops-chart-card ops-card-stays">
      <header>
        <h3>Top Performing Stays</h3>
        <a href="/ops/reports/">View all</a>
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
              <th>Stay / Listing</th>
              <th>Revenue</th>
              <th>Occupancy</th>
              <th>ADR</th>
              <th>Rating</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            {stays.map((s) => (
              <tr key={s.listing}>
                <td>
                  <div className="ops-stay-cell">
                    <img src={s.imgSrc} className="ops-thumb" alt={s.listing} referrerPolicy="no-referrer" />
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
                <td><span className={s.delta === '—' ? 'td-flat' : s.delta.startsWith('-') ? 'td-down' : 'td-up'}>{s.delta}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="ops-stays-foot">
        <span>Showing 1 to 5 of 12 stays</span>
        <div className="ops-pager">
          <button type="button" aria-label="Previous page"><ChevronLeft size={13} /></button>
          <button type="button" className="is-active">1</button>
          <button type="button">2</button>
          <button type="button">3</button>
          <button type="button" aria-label="Next page"><ChevronRight size={13} /></button>
        </div>
      </div>
    </article>
  );
}

function InsightsCard() {
  return (
    <article className="ops-chart-card ops-card-insights">
      <header>
        <h3><Sparkles size={17} />AI Insights</h3>
        <span className="ops-beta">Beta</span>
      </header>
      <div className="ops-ins-list">
        {insights.map(({ title, body, tone, Icon }) => (
          <div key={title} className={`ops-ins ops-ins--${tone}`}>
            <span className="ops-ins__ico"><Icon size={14} /></span>
            <div>
              <strong>{title}</strong>
              <p>{body}</p>
            </div>
          </div>
        ))}
      </div>
      <a href="/ops/reports/" className="ops-ins-more">View more insights</a>
      <div className="ops-ins-foot">
        <Clock3 size={12} /><span>Auto-updated just now</span>
      </div>
    </article>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function OpsReportsPage() {
  return (
    <main className="dashboard-content ops-page ops-rpt">

      {/* ── Hero ── */}
      <div className="ops-rpt-hero">
        <div>
          <h2>Reports &amp; Analytics</h2>
          <p className="ops-rpt-hero__subtitle">Measure occupancy, revenue, maintenance costs, booking sources, and operational performance.</p>
        </div>
        <div className="ops-rpt-hero__btns">
          <button type="button" className="ops-btn-date">
            <CalendarRange size={15} />Jun 6 – Jun 12, 2026<ChevronDown size={13} />
          </button>
          <button type="button" className="ops-btn-sec"><Filter size={14} />Filters</button>
          <button type="button" className="ops-btn-sec"><Download size={14} />Export</button>
        </div>
      </div>

      {/* ── KPI row ── */}
      <div className="ops-kpis" aria-label="Summary metrics">
        {metrics.map((m) => <MetricCard key={m.label} m={m} />)}
      </div>

      {/* ── Charts row ── */}
      <div className="ops-charts-row">
        <RevenueChart />
        <ChannelsCard />
        <DonutCard />
      </div>

      {/* ── Bottom row ── */}
      <div className="ops-bottom-row">
        <HeatmapCard />
        <StaysCard />
        <InsightsCard />
      </div>

    </main>
  );
}
