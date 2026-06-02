import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, BarChart3, CalendarDays, Search, Sparkles } from 'lucide-react';
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
  return (
    <article className="ops-chart-card" data-report-card>
      <div className="ops-card-heading">
        <div>
          <span>{chart.category}</span>
          <h3>{chart.title}</h3>
        </div>
        <strong>{chart.maxTotal}</strong>
      </div>
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
    </article>
  );
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
          <h2>Every signal we track, cleaned up into fast visual cards.</h2>
          <p>Reservations, visits, agent questions, feedback, invoices, deposits, donations, coupons, promotions, listings, and calendar setup all stay connected to Django data.</p>
        </div>
        <div className="ops-hero-actions">
          <a href={snapshot.calendarUrl}><CalendarDays size={16} /> Business calendar</a>
          <a href="/ops/admin/"><BarChart3 size={16} /> Admin command</a>
        </div>
      </section>

      <section className="ops-metric-grid">
        {snapshot.summaryCards.map((card) => (
          <article key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.caption}</p>
          </article>
        ))}
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

      <section className="ops-chart-grid">
        {charts.map((chart) => <ChartCard chart={chart} key={chart.id} />)}
      </section>
    </main>
  );
}
