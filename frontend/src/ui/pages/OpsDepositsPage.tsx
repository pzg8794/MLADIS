import { useEffect, useMemo, useState } from 'react';
import {
  BadgeAlert,
  BadgeCheck,
  BadgeDollarSign,
  CalendarClock,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Download,
  FileText,
  LucideIcon,
  Phone,
  Search,
  SlidersHorizontal,
  X,
} from 'lucide-react';
import { OpsDepositHoldsFactory } from '../../application/OpsDepositHoldsFactory';
import {
  DepositHold,
  DepositHoldsSnapshot,
  DepositMetric,
  ExpiringDepositHold,
  type DepositHoldAction,
  type DepositHoldTone,
  type DepositRiskTone,
  type DepositStatusTone,
} from '../../domain/depositHolds';
import './ops-deposits-page.css';

const metricIcons: Record<DepositHoldTone, LucideIcon> = {
  green: BadgeDollarSign,
  orange: CalendarClock,
  blue: BadgeCheck,
  red: BadgeAlert,
  purple: BadgeDollarSign,
};

function DepositSparkline({ metric }: { metric: DepositMetric }) {
  return (
    <svg className="deposit-v4-sparkline" viewBox="0 0 220 52" preserveAspectRatio="none" aria-hidden="true">
      <path className="deposit-v4-sparkline__line" d={metric.points} />
    </svg>
  );
}

function DepositMetricCard({ metric }: { metric: DepositMetric }) {
  const Icon = metricIcons[metric.tone];
  return (
    <article className={`deposit-v4-metric deposit-v4-tone--${metric.tone}`}>
      <header>
        <span className="deposit-v4-icon"><Icon size={18} /></span>
        <small>{metric.label}</small>
      </header>
      <strong>{metric.value}</strong>
      <em>{metric.trend}</em>
      <DepositSparkline metric={metric} />
    </article>
  );
}

function avatarTone(row: DepositHold): DepositHoldTone {
  if (row.statusTone === 'failed') return 'red';
  if (row.riskTone === 'medium') return 'orange';
  if (row.source === 'stay') return 'blue';
  return 'green';
}

function Avatar({ initials, tone }: { initials: string; tone: DepositHoldTone }) {
  return <span className={`deposit-v4-avatar deposit-v4-avatar--${tone}`}>{initials}</span>;
}

function StatusBadge({ label, tone }: { label: string; tone: DepositStatusTone }) {
  return <span className={`deposit-v4-status deposit-v4-status--${tone}`}>{label}</span>;
}

function RiskBadge({ label, tone }: { label: string; tone: DepositRiskTone }) {
  return <span className={`deposit-v4-risk deposit-v4-risk--${tone}`}>{label}</span>;
}

function DepositsTable({
  selectedId,
  onSelect,
  visibleRows,
  query,
  onQueryChange,
}: {
  selectedId: string;
  onSelect: (id: string) => void;
  visibleRows: DepositHold[];
  query: string;
  onQueryChange: (query: string) => void;
}) {
  return (
    <section className="deposit-v4-table-card">
      <div className="deposit-v4-table-toolbar">
        <label className="deposit-v4-search">
          <Search size={15} />
          <input
            aria-label="Search deposits"
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search by guest name, email, reservation #..."
            value={query}
          />
          <kbd>⌘ F</kbd>
        </label>
        <button className="deposit-v4-filter-button" type="button"><SlidersHorizontal size={15} /> More filters</button>
      </div>

      <div className="deposit-v4-table-scroll">
        <table>
          <thead>
            <tr>
              <th className="deposit-v4-check-cell"><span className="deposit-v4-check" /></th>
              <th>Guest</th>
              <th>Reservation</th>
              <th>Listing</th>
              <th>Hold Amount</th>
              <th>Requested Date <span aria-hidden="true">↓</span></th>
              <th>Expiration</th>
              <th>Risk</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row) => (
              <tr className={row.id === selectedId ? 'is-selected' : ''} key={row.id} onClick={() => onSelect(row.id)}>
                <td className="deposit-v4-check-cell">
                  <button className={`deposit-v4-check ${row.id === selectedId ? 'is-checked' : ''}`} type="button" aria-label={`Select ${row.guestName}`}>
                    {row.id === selectedId && <CheckCircle2 size={13} />}
                  </button>
                </td>
                <td>
                  <div className="deposit-v4-guest-cell">
                    <Avatar initials={row.initials} tone={avatarTone(row)} />
                    <span><strong>{row.guestName}</strong><small>{row.email}</small></span>
                  </div>
                </td>
                <td><strong>{row.holdNumber}</strong><small>{row.reservation.number}</small></td>
                <td>{row.reservation.listing}</td>
                <td><strong>{row.money.display}</strong><small>{row.money.currency}</small></td>
                <td>{row.requestedDate}<small>{row.requestedTime}</small></td>
                <td>{row.expirationDate}<small>{row.expirationTime}</small>{row.hasWarning && <i className="deposit-v4-warning">!</i>}</td>
                <td><RiskBadge label={row.risk} tone={row.riskTone} /></td>
                <td><StatusBadge label={row.statusLabel} tone={row.statusTone} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer className="deposit-v4-table-footer">
        <span>Showing {visibleRows.length ? 1 : 0} to {visibleRows.length} of {visibleRows.length} results</span>
        <nav aria-label="Deposit pagination">
          <button type="button" aria-label="Previous page"><ChevronLeft size={16} /></button>
          <button className="is-active" type="button">1</button>
          <button type="button">2</button>
          <button type="button">3</button>
          <button type="button">4</button>
          <button type="button" aria-label="Next page"><ChevronRight size={16} /></button>
        </nav>
      </footer>
    </section>
  );
}

function ExpiringSoonPanel({ holds, onSelect }: { holds: ExpiringDepositHold[]; onSelect: (id: string) => void }) {
  return (
    <section className="deposit-v4-expiring">
      <header>
        <h2><Clock3 size={17} /> Expiring Soon</h2>
        <a href="/ops/deposits/">View all ({holds.length})</a>
      </header>
      <div>
        {holds.map((item) => (
          <article key={item.id} onClick={() => onSelect(item.id)}>
            <i />
            <span><strong>{item.guest}</strong><small>{item.listing}</small></span>
            <em>{item.timeLeft}</em>
          </article>
        ))}
      </div>
    </section>
  );
}

function EmptyDetailPanel() {
  return (
    <aside className="deposit-v4-detail">
      <section className="deposit-v4-person-card">
        <h2>Select a deposit hold</h2>
        <p className="deposit-v4-muted">Choose a row to review authorization state, timeline, payment attempts, and allowed actions.</p>
      </section>
    </aside>
  );
}

function SelectedDepositPanel({
  selected,
  onClose,
  onAction,
  busyAction,
}: {
  selected: DepositHold;
  onClose: () => void;
  onAction: (action: DepositHoldAction) => void;
  busyAction: DepositHoldAction | '';
}) {
  const firstAttempt = selected.paymentAttempts[0];
  return (
    <aside className="deposit-v4-detail">
      <section className="deposit-v4-person-card">
        <button className="deposit-v4-close" onClick={onClose} type="button" aria-label="Close selected deposit"><X size={17} /></button>
        <div className="deposit-v4-person-head">
          <Avatar initials={selected.initials} tone={avatarTone(selected)} />
          <div>
            <h2>{selected.guestName}</h2>
            <p>{selected.email}</p>
            <span>
              <Phone size={13} />
              {selected.phone || 'Phone not on file'}
              {selected.repeatGuest && <b>Repeat guest</b>}
            </span>
          </div>
        </div>

        <article className="deposit-v4-reservation-card">
          <img src={selected.reservation.imageUrl} alt={selected.reservation.listing} />
          <div>
            <small>Reservation <strong>{selected.holdNumber}</strong></small>
            <h3>{selected.reservation.listing}</h3>
            <p>{selected.reservation.dateRange} • {selected.reservation.nightsLabel}</p>
          </div>
        </article>

        <section className="deposit-v4-hold-facts">
          <div><small>Hold Amount</small><strong>{selected.money.withCurrency}</strong><StatusBadge label={selected.statusLabel} tone={selected.statusTone} /></div>
          <div><small>Requested</small><span>{selected.requestedDate} at {selected.requestedTime}</span></div>
          <div><small>Expires</small><span>{selected.expirationDate} at {selected.expirationTime} <em>({selected.expirationTimeLeft})</em></span></div>
        </section>

        <section className="deposit-v4-timeline">
          <h3>Authorization Timeline</h3>
          <ol>
            {selected.timeline.map((item) => (
              <li className={`deposit-v4-tone--${item.tone}`} key={`${selected.id}-${item.title}`}>
                <i />
                <div><strong>{item.title}</strong><small>{item.timestamp}</small></div>
                <p>{item.note}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="deposit-v4-payment">
          <header>
            <h3>Linked Payment Attempts</h3>
            <a href="/ops/payments/">View all</a>
          </header>
          {firstAttempt ? (
            <article>
              <span className="deposit-v4-card-brand">{firstAttempt.brand}</span>
              <div><strong>{firstAttempt.method}</strong><StatusBadge label={firstAttempt.status} tone={firstAttempt.statusTone} /></div>
              <time>{firstAttempt.timestamp}</time>
              <small>Auth ID: {firstAttempt.authId} <b>{firstAttempt.amount.withCurrency}</b></small>
            </article>
          ) : (
            <p className="deposit-v4-muted">No provider attempt has been linked yet.</p>
          )}
        </section>

        <section className="deposit-v4-note">
          <h3>Guest Note</h3>
          <p>{selected.notes || 'No guest note recorded for this hold.'}</p>
        </section>

        <section className="deposit-v4-actions">
          <button
            className="deposit-v4-primary"
            disabled={!selected.canApprove || busyAction === 'approve'}
            onClick={() => onAction('approve')}
            type="button"
          >
            {busyAction === 'approve' ? 'Approving...' : 'Approve hold'}
          </button>
          <div>
            <button disabled={!selected.canRelease || busyAction === 'release'} onClick={() => onAction('release')} type="button">
              {busyAction === 'release' ? 'Releasing...' : 'Release hold'}
            </button>
            <button disabled={!selected.canRequestGuestAction || busyAction === 'request-guest-action'} onClick={() => onAction('request-guest-action')} type="button">
              Request guest action
            </button>
          </div>
          <a className="deposit-v4-action-link" href={selected.adminUrl}><FileText size={14} /> Generate receipt</a>
        </section>
      </section>
    </aside>
  );
}

export function OpsDepositsPage() {
  const service = useMemo(() => OpsDepositHoldsFactory.create(), []);
  const [snapshot, setSnapshot] = useState<DepositHoldsSnapshot | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [query, setQuery] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busyAction, setBusyAction] = useState<DepositHoldAction | ''>('');

  useEffect(() => {
    service.loadDeposits()
      .then((nextSnapshot) => {
        setSnapshot(nextSnapshot);
        setSelectedId((current) => current || nextSnapshot.rows[0]?.id || '');
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load deposits.'));
  }, [service]);

  const visibleRows = useMemo(() => (
    snapshot ? service.filterDeposits(snapshot.rows, query) : []
  ), [query, service, snapshot]);

  useEffect(() => {
    if (!snapshot) return;
    if (selectedId && snapshot.rows.some((row) => row.id === selectedId)) return;
    if (selectedId) setSelectedId(snapshot.rows[0]?.id || '');
  }, [selectedId, snapshot]);

  const selected = snapshot?.rows.find((row) => row.id === selectedId) || null;

  async function applyAction(action: DepositHoldAction) {
    if (!selected) return;
    setBusyAction(action);
    setMessage('');
    setError('');
    try {
      const nextSnapshot = await service.applyAction(selected, action);
      setSnapshot(nextSnapshot);
      setSelectedId(selected.id);
      setMessage(`${selected.holdNumber} updated.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update that deposit hold.');
    } finally {
      setBusyAction('');
    }
  }

  if (error && !snapshot) {
    return (
      <main className="dashboard-content deposit-v4-page">
        <section className="dashboard-error">{error}</section>
      </main>
    );
  }

  if (!snapshot) {
    return (
      <main className="dashboard-content deposit-v4-page">
        <section className="deposit-v4-person-card">Loading deposits...</section>
      </main>
    );
  }

  return (
    <main className="dashboard-content deposit-v4-page">
      <section className="deposit-v4-titlebar">
        <div>
          <h1>Deposits &amp; Holds</h1>
          <p>Manage security deposits, authorization holds, releases, and exceptions.</p>
        </div>
        <div className="deposit-v4-title-actions">
          <button type="button"><CalendarDays size={16} /> Jun 6 – Jun 12, 2026 <ChevronDown size={15} /></button>
          <button type="button"><SlidersHorizontal size={16} /> Filters</button>
          <button type="button"><Download size={16} /> Export</button>
        </div>
      </section>

      {message && <div className="deposit-v4-alert deposit-v4-alert--success">{message}</div>}
      {error && <div className="deposit-v4-alert deposit-v4-alert--error">{error}</div>}

      <section className="deposit-v4-summary-row">
        <div className="deposit-v4-metric-grid">
          {snapshot.summaryCards.map((metric) => <DepositMetricCard metric={metric} key={metric.label} />)}
        </div>
        <ExpiringSoonPanel holds={snapshot.expiringHolds} onSelect={setSelectedId} />
      </section>

      <section className="deposit-v4-workspace">
        <DepositsTable
          selectedId={selectedId}
          onSelect={setSelectedId}
          visibleRows={visibleRows}
          query={query}
          onQueryChange={setQuery}
        />
        {selected ? (
          <SelectedDepositPanel
            selected={selected}
            onClose={() => setSelectedId('')}
            onAction={applyAction}
            busyAction={busyAction}
          />
        ) : (
          <EmptyDetailPanel />
        )}
      </section>
    </main>
  );
}
