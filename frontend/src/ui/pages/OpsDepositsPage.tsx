import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CreditCard, ExternalLink, ReceiptText, Search, ShieldCheck } from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsDepositsSnapshot } from '../../domain/models';

function statusTone(status: string) {
  if (status === 'requires_capture') return 'authorized';
  if (status === 'captured') return 'captured';
  if (status === 'failed') return 'failed';
  if (status === 'canceled') return 'released';
  return 'pending';
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

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page">
      <section className="ops-hero ops-hero--deposits">
        <div>
          <span><CreditCard size={16} /> Deposit command center</span>
          <h2>Security deposit holds without the old admin-table feel.</h2>
          <p>Review Stripe and PayPal deposit records, active holds, captured value, failed attempts, and the booking record behind each hold.</p>
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
              {option.label}
              <small>{option.count}</small>
            </button>
          ))}
        </div>
      </section>

      <section className="ops-table-card">
        <div className="ops-card-heading">
          <div>
            <span>Deposit ledger</span>
            <h3>{rows.length} records shown</h3>
          </div>
          <strong>$200</strong>
        </div>

        {rows.length === 0 && (
          <article className="ops-empty-state">
            <ShieldCheck size={28} />
            <h3>No deposits match that view.</h3>
            <p>Clear the search or switch to a different status.</p>
          </article>
        )}

        {rows.map((row) => (
          <article className="ops-data-row ops-data-row--deposits" key={row.id}>
            <div>
              <span className={`ops-status-pill ops-status-pill--${statusTone(row.status)}`}>{row.statusLabel}</span>
              <h3>{row.guestName}</h3>
              <p>{row.email || 'No email captured'}</p>
            </div>
            <div>
              <strong>{row.stayName}</strong>
              <p>{row.createdLabel || 'Date pending'} · {row.provider}</p>
            </div>
            <div>
              <strong>{row.amount}</strong>
              <p>{row.notes || 'No internal notes yet.'}</p>
            </div>
            <div className="ops-row-actions">
              {row.checkoutUrl && <a href={row.checkoutUrl} target="_blank" rel="noreferrer">Checkout</a>}
              {row.inquiryAdminUrl && <a href={row.inquiryAdminUrl}>Booking</a>}
              <a href={row.adminUrl}>Record</a>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
