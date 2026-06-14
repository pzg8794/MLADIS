import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ChevronRight, ExternalLink, Mail, Search, Send, ShieldCheck, Users } from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsCustomerRow, OpsCustomersSnapshot } from '../../domain/models';
import { OpsRecordSection } from '../components/OpsRecordSection';

function contact(row: { email: string; phone: string }) {
  if (row.email && row.phone) return `${row.email} · ${row.phone}`;
  if (row.email) return row.email;
  if (row.phone) return row.phone;
  return 'Needs contact details';
}

export function OpsCustomersPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsCustomersSnapshot | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState(new URLSearchParams(window.location.search).get('segment') || '');

  useEffect(() => {
    let mounted = true;
    service
      .loadCustomers()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load customers.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const rows = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    return snapshot.rows.filter((row) => {
      const matchesSegment = !segment || row.segmentValue === segment;
      const matchesSearch = !query || [
        row.name,
        row.email,
        row.phone,
        row.segment,
        row.source,
        row.lastStay,
        row.notes,
      ].some((value) => value.toLowerCase().includes(query));
      return matchesSegment && matchesSearch;
    });
  }, [search, segment, snapshot]);

  const renderCustomerRow = (row: OpsCustomerRow) => (
    <details className="ops-data-row ops-data-row--customers ops-expand-card" data-segment={row.segmentValue || 'average'} key={row.id}>
      <summary className="ops-data-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <div>
          <span className={`ops-status-pill ops-status-pill--${row.segmentValue || 'average'}`}>{row.segment}</span>
          <h3>{row.name}</h3>
          <p>{contact(row)}</p>
        </div>
        <div>
          <strong>{row.lastStay}</strong>
          <p>{row.source} · {row.marketingConsent}</p>
        </div>
        <div className="ops-mini-stats">
          <span>{row.directReservations} direct</span>
          <span>{row.airbnbReservations} Airbnb</span>
        </div>
      </summary>
      <div className="ops-expand-details">
        <div className="ops-mini-stats">
          <span>{row.feedbackCount} feedback</span>
          <span>{row.invoiceCount} invoices</span>
        </div>
        <div>
          <span>Notes</span>
          <p>{row.notes || 'No notes captured yet.'}</p>
        </div>
        <div className="ops-row-actions">
          {row.email && <a href={`mailto:${row.email}`}><Mail size={14} /> Email</a>}
          {row.canReceivePromotions && <a href="/admin/bookings/promotion/add/"><Send size={14} /> Promote</a>}
          <a href={row.adminUrl}>Profile</a>
        </div>
      </div>
    </details>
  );

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page">
      <section className="ops-hero ops-hero--customers">
        <div>
          <span><Users size={16} /> Modern customer CRM</span>
          <h2>Customers CRM</h2>
          <p>Guest profiles, feedback, groups, and promotion readiness in one compact view.</p>
        </div>
        <div className="ops-hero-actions">
          <a href={snapshot.adminUrl}><ExternalLink size={16} /> Customer admin</a>
          <a href="/ops/reservations/"><ShieldCheck size={16} /> Reservations CRM</a>
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
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search customers, contacts, segments, notes..." />
        </label>
        <div className="ops-chip-row">
          {snapshot.segmentOptions.map((option) => (
            <button className={segment === option.value ? 'is-active' : ''} data-segment={option.value || 'all'} key={option.value || 'all'} onClick={() => setSegment(option.value)} type="button">
              {option.label}
              <small>{option.count}</small>
            </button>
          ))}
        </div>
      </section>

      <OpsRecordSection
        rows={rows}
        renderRow={renderCustomerRow}
        eyebrow="Customer list"
        title={`${rows.length} customers shown`}
        subtitle={`${snapshot.rows.length} total customers available.`}
        modalTitle={`${rows.length} customers shown`}
        modalSubtitle="Scroll customer profiles, consent state, history, and actions without stretching the page."
        aside={<strong>{snapshot.rows.length}</strong>}
        emptyState={(
          <article className="ops-empty-state">
            <Users size={28} />
            <h3>No customers match that filter.</h3>
            <p>Clear the search or choose another customer group.</p>
          </article>
        )}
      />
    </main>
  );
}
