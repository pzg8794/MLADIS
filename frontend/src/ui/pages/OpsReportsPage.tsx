import { CSSProperties, useEffect, useMemo, useState } from 'react';
import { AlertCircle, BarChart3, CalendarDays, ChevronRight, Search, Sparkles } from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsChart, OpsReportsSnapshot } from '../../domain/models';

const reportFilters = [
  { label: 'All', value: '' },
  { label: 'Booking', value: 'booking' },
  { label: 'Money', value: 'money' },
  { label: 'Customers', value: 'customers' },
  { label: 'Traffic', value: 'traffic' },
  { label: 'Agent', value: 'agent' },
  { label: 'Calendar', value: 'calendar' },
];

function readableDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value));
}

function ChartCard({ chart }: { chart: OpsChart }) {
  const isTimeline = chart.id.includes('timeline');
  return (
    <details className={`ops-chart-card ops-expand-card ${isTimeline ? 'ops-chart-card--timeline' : ''}`} data-report-card>
      <summary className="ops-card-heading">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <div>
          <span>Report</span>
          <h3>{chart.title}</h3>
        </div>
        <strong>{chart.maxTotal}</strong>
      </summary>
      {isTimeline ? (
        <div className="ops-timeline-chart">
          {chart.rows.length === 0 && <p>No data captured yet.</p>}
          {chart.rows.map((row) => (
            <div className="ops-timeline-day" key={`${chart.id}-${row.label}`}>
              <i style={{ height: `${row.width}%` }} />
              <strong>{row.total}</strong>
              <span>{row.label}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="ops-chart-bars">
          {chart.rows.length === 0 && <p>No data captured yet.</p>}
          {chart.rows.map((row) => (
            <div className="ops-chart-row" key={`${chart.id}-${row.label}`}>
              <span>{row.label}</span>
              <div>
                <i style={{ width: `${row.width}%` }} />
              </div>
              <strong>{row.total}</strong>
            </div>
          ))}
        </div>
      )}
    </details>
  );
}

type ReportChartGroup = {
  key: string;
  label: string;
  tone: string;
  charts: OpsChart[];
};

const reportGroupMeta: Record<string, { label: string; tone: string }> = {
  booking: { label: 'Booking', tone: '#6f55b5' },
  money: { label: 'Money', tone: '#0b78b6' },
  customers: { label: 'Customers', tone: '#087b2d' },
  traffic: { label: 'Traffic', tone: '#c95705' },
  agent: { label: 'Agent', tone: '#b4235c' },
  calendar: { label: 'Calendar', tone: '#2563eb' },
};

const reportGroupOrder = ['booking', 'money', 'customers', 'traffic', 'agent', 'calendar'];

function groupReportCharts(charts: OpsChart[]): ReportChartGroup[] {
  const grouped = new Map<string, OpsChart[]>();
  charts.forEach((chart) => {
    const key = chart.category || 'booking';
    grouped.set(key, [...(grouped.get(key) || []), chart]);
  });

  const orderedKeys = [
    ...reportGroupOrder.filter((key) => grouped.has(key)),
    ...Array.from(grouped.keys()).filter((key) => !reportGroupOrder.includes(key)).sort(),
  ];

  return orderedKeys.map((key) => {
    const meta = reportGroupMeta[key] || { label: key.charAt(0).toUpperCase() + key.slice(1), tone: '#6f55b5' };
    return { key, label: meta.label, tone: meta.tone, charts: grouped.get(key) || [] };
  });
}

export function OpsReportsPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsReportsSnapshot | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('');

  useEffect(() => {
    let mounted = true;
    service
      .loadReports()
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

  const charts = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    return snapshot.charts.filter((chart) => {
      const matchesFilter = !filter || chart.category === filter;
      const matchesSearch = !query || chart.title.toLowerCase().includes(query) || chart.rows.some((row) => row.label.toLowerCase().includes(query));
      return matchesFilter && matchesSearch;
    });
  }, [filter, search, snapshot]);
  const chartGroups = useMemo(() => groupReportCharts(charts), [charts]);

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page">
      <section className="ops-hero ops-hero--reports">
        <div>
          <span><BarChart3 size={16} /> Modern reports</span>
          <h2>Reports</h2>
          <p>Reservations, revenue, customers, visits, agent questions, campaigns, and calendar health.</p>
        </div>
        <div className="ops-hero-actions">
          <a href={snapshot.calendarUrl}><CalendarDays size={16} /> Business calendar</a>
          <a href="/ops/admin/"><BarChart3 size={16} /> Admin command</a>
        </div>
      </section>

      <section className="ops-toolbar">
        <label>
          <Search size={17} />
          <input id="report-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search reports, deposits, visits, agent..." />
        </label>
        <div className="ops-chip-row">
          <span><Sparkles size={15} /> {readableDate(snapshot.reportSince)} - {readableDate(snapshot.reportUntil)}</span>
          {reportFilters.map((item) => (
            <button className={filter === item.value ? 'is-active' : ''} data-report-filter={item.value || 'all'} key={item.value || 'all'} onClick={() => setFilter(item.value)} type="button">
              {item.label}
            </button>
          ))}
        </div>
      </section>

      <section className="ops-report-category-groups" aria-label="Report groups">
        {chartGroups.map((group) => (
          <details className="ops-report-group ops-expand-card" key={group.key} style={{ '--report-tone': group.tone } as CSSProperties}>
            <summary className="ops-card-heading">
              <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
              <div>
                <span>Report group</span>
                <h3>{group.label}</h3>
              </div>
              <strong>{group.charts.length}</strong>
            </summary>
            <div className="ops-report-category-group__cards">
              {group.charts.map((chart) => <ChartCard chart={chart} key={chart.id} />)}
            </div>
          </details>
        ))}
        {chartGroups.length === 0 && (
          <article className="ops-empty-state">
            <BarChart3 size={28} />
            <h3>No reports match this view.</h3>
            <p>Clear the search or choose another report category.</p>
          </article>
        )}
      </section>
    </main>
  );
}
