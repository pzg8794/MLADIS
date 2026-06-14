import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ChevronRight, CreditCard, ExternalLink, ReceiptText, Search, ShieldCheck } from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsDepositRow, OpsDepositsSnapshot } from '../../domain/models';
import { OpsRecordSection } from '../components/OpsRecordSection';
import { formatStayName } from '../helpers/stayNames';

function statusTone(status: string) {
  if (status === 'requires_capture') return 'authorized';
  if (status === 'captured') return 'captured';
  if (status === 'failed') return 'failed';
  if (status === 'canceled') return 'released';
  return 'pending';
}

function compactStatusLabel(label: string) {
  return label
    .replace('Requires payment configuration', 'To configure')
    .replace('Requires capture', 'Capture')
    .replace('Checkout created', 'Checkout')
    .replace('Payment failed', 'Failed')
    .replace('Canceled', 'Released');
}

export function OpsDepositsPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsDepositsSnapshot | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    let mounted = true;
    service
      .loadDeposits()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load deposits.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const rows = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    return snapshot.rows.filter((row) => {
      const matchesStatus = !status || row.status === status;
      const matchesSearch = !query || [row.guestName, row.email, row.stayName, row.provider, row.statusLabel, row.notes].some((value) => value.toLowerCase().includes(query));
      return matchesStatus && matchesSearch;
    });
  }, [search, snapshot, status]);

  const renderDepositRow = (row: OpsDepositRow) => (
    <details className="ops-data-row ops-data-row--deposits ops-expand-card" data-status={statusTone(row.status)} key={row.id}>
      <summary className="ops-data-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <div>
          <span className={`ops-status-pill ops-status-pill--${statusTone(row.status)}`}>{row.statusLabel}</span>
          <h3>{row.guestName}</h3>
          <p>{row.email || 'No email captured'}</p>
        </div>
        <div>
          <strong>{formatStayName(row.stayName)}</strong>
          <p>{row.createdLabel || 'Date pending'} · {row.provider}</p>
        </div>
        <div>
          <strong>{row.amount}</strong>
          <p>{row.notes || 'No internal notes yet.'}</p>
        </div>
      </summary>
      <div className="ops-expand-details">
        <div>
          <span>Workflow</span>
          <p>{row.statusLabel} via {row.provider}. Capture-ready holds are authorized deposits waiting for an admin capture or release decision.</p>
        </div>
        <div className="ops-row-actions">
          {row.checkoutUrl && <a href={row.checkoutUrl} target="_blank" rel="noreferrer">Checkout</a>}
          {row.inquiryAdminUrl && <a href={row.inquiryAdminUrl}>Booking</a>}
          <a href={row.adminUrl}>Record</a>
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
    <main className="dashboard-content ops-page ops-page--deposits">
      <section className="ops-hero ops-hero--deposits">
        <div>
          <span><CreditCard size={16} /> Deposit command center</span>
          <h2>Deposits</h2>
          <p>Review security holds, captures, failed attempts, and the booking record behind each hold.</p>
        </div>
        <div className="ops-hero-actions">
          <a href={snapshot.adminUrl}><ExternalLink size={16} /> Deposit admin</a>
          <a href="/admin/bookings/damagedeposit/add/"><ReceiptText size={16} /> Add record</a>
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
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search deposits, guests, stays, providers..." />
        </label>
        <div className="ops-chip-row">
          {snapshot.statusOptions.map((option) => (
            <button className={status === option.value ? 'is-active' : ''} key={option.value || 'all'} onClick={() => setStatus(option.value)} type="button">
              {compactStatusLabel(option.label)}
              <small>{option.count}</small>
            </button>
          ))}
        </div>
      </section>

      <OpsRecordSection
        rows={rows}
        renderRow={renderDepositRow}
        eyebrow="Deposit ledger"
        title={`${rows.length} records shown`}
        subtitle={`${snapshot.rows.length} total deposits available in this workspace.`}
        modalTitle={`${rows.length} deposit records shown`}
        modalSubtitle="Scroll the security deposit ledger, capture state, booking links, and provider actions."
        actionLabel="Open ledger"
        aside={<strong>$200 hold</strong>}
        emptyState={(
          <article className="ops-empty-state">
            <ShieldCheck size={28} />
            <h3>No deposits match that view.</h3>
            <p>Clear the search or switch to a different status.</p>
          </article>
        )}
      />
    </main>
  );
}
