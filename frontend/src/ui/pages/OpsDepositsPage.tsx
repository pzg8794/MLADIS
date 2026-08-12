import { useEffect, useMemo, useState } from 'react';
import {
  BadgeAlert,
  BadgeCheck,
  BadgeDollarSign,
  CalendarClock,
  CheckCircle2,
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
  DepositStatusOption,
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
      <div className="deposit-v4-metric-body">
        <span className="deposit-v4-icon"><Icon size={18} /></span>
        <div>
          <small>{metric.label}</small>
          <strong>{metric.value}</strong>
          <em>{metric.trend}</em>
        </div>
      </div>
      {metric.points && <DepositSparkline metric={metric} />}
    </article>
  );
}

function csvCell(value: string | number): string {
  const normalized = String(value ?? '');
  return /[",\n]/.test(normalized) ? `"${normalized.replace(/"/g, '""')}"` : normalized;
}

function exportDepositLedger(rows: DepositHold[]) {
  const headings = ['Hold', 'Guest', 'Email', 'Reservation', 'Listing', 'Amount', 'Currency', 'Status', 'Requested', 'Expiration'];
  const body = rows.map((row) => [
    row.holdNumber,
    row.guestName,
    row.email,
    row.reservation.requestKey || row.reservation.number,
    row.reservation.listing,
    row.money.display,
    row.money.currency,
    row.statusLabel,
    `${row.requestedDate} ${row.requestedTime}`.trim(),
    `${row.expirationDate} ${row.expirationTime}`.trim(),
  ]);
  const csv = [headings, ...body].map((line) => line.map(csvCell).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `mladis-deposit-holds-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
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
  rows,
  totalRows,
  page,
  totalPages,
  pageStart,
  pageEnd,
  status,
  statusOptions,
  query,
  onQueryChange,
  onStatusChange,
  onPageChange,
}: {
  selectedId: string;
  onSelect: (id: string) => void;
  rows: DepositHold[];
  totalRows: number;
  page: number;
  totalPages: number;
  pageStart: number;
  pageEnd: number;
  status: string;
  statusOptions: DepositStatusOption[];
  query: string;
  onQueryChange: (query: string) => void;
  onStatusChange: (status: string) => void;
  onPageChange: (page: number) => void;
}) {
  const pageNumbers = Array.from({ length: totalPages }, (_, index) => index + 1);

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
        <label className="deposit-v4-status-filter">
          <SlidersHorizontal size={15} />
          <select
            id="deposit-status-filter"
            aria-label="Filter deposits by status"
            onChange={(event) => onStatusChange(event.target.value)}
            value={status}
          >
            {statusOptions.map((option) => (
              <option key={option.value || 'all'} value={option.value}>
                {option.label} ({option.count})
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="deposit-v4-table-scroll">
        <table>
          <colgroup>
            <col style={{ width: '34px' }} />
            <col style={{ width: '19%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '20%' }} />
            <col style={{ width: '12%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '8%' }} />
            <col style={{ width: '10%' }} />
          </colgroup>
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
            {rows.map((row) => (
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
                <td><strong title={row.fullHoldLabel}>{row.holdDisplayNumber}</strong><small>{row.reservation.number}</small></td>
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
        <span>Showing {pageStart} to {pageEnd} of {totalRows} results</span>
        {totalPages > 1 && (
          <nav aria-label="Deposit pagination">
            <button
              type="button"
              aria-label="Previous page"
              disabled={page === 1}
              onClick={() => onPageChange(page - 1)}
            >
              <ChevronLeft size={16} />
            </button>
            {pageNumbers.map((pageNumber) => (
              <button
                className={pageNumber === page ? 'is-active' : ''}
                key={pageNumber}
                type="button"
                onClick={() => onPageChange(pageNumber)}
              >
                {pageNumber}
              </button>
            ))}
            <button
              type="button"
              aria-label="Next page"
              disabled={page === totalPages}
              onClick={() => onPageChange(page + 1)}
            >
              <ChevronRight size={16} />
            </button>
          </nav>
        )}
      </footer>
    </section>
  );
}

function ExpiringSoonPanel({ holds, onSelect }: { holds: ExpiringDepositHold[]; onSelect: (id: string) => void }) {
  const visibleHolds = holds.slice(0, 3);
  return (
    <section className="deposit-v4-expiring">
      <header>
        <h2><Clock3 size={17} /> Expiry Attention</h2>
        <a href="/ops/deposits/">View all ({holds.length})</a>
      </header>
      <div>
        {visibleHolds.map((item) => (
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
  const actionDisabledReason = `This action is unavailable while the hold is ${selected.statusLabel.toLowerCase()}.`;
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
          <img
            src={selected.reservation.displayImageUrl}
            alt={selected.reservation.listing}
            onError={(event) => {
              event.currentTarget.src = selected.reservation.imageFallbackUrl;
            }}
          />
          <div>
            <small>Reservation <strong title={selected.fullHoldLabel}>{selected.holdDisplayNumber}</strong></small>
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
            {firstAttempt && (
              <a href={firstAttempt.paymentUrl}>
                {firstAttempt.canOpenPayment ? 'View payment' : 'View payments workspace'}
              </a>
            )}
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
            title={!selected.canApprove ? actionDisabledReason : ''}
            type="button"
          >
            {busyAction === 'approve' ? 'Approving...' : 'Approve hold'}
          </button>
          <div>
            <button
              disabled={!selected.canRelease || busyAction === 'release'}
              onClick={() => onAction('release')}
              title={!selected.canRelease ? actionDisabledReason : ''}
              type="button"
            >
              {busyAction === 'release' ? 'Releasing...' : 'Release hold'}
            </button>
            <button
              disabled={!selected.canRequestGuestAction || busyAction === 'request-guest-action'}
              onClick={() => onAction('request-guest-action')}
              title={!selected.canRequestGuestAction ? actionDisabledReason : ''}
              type="button"
            >
              Request guest action
            </button>
          </div>
          {selected.receipt.canGenerate && selected.receipt.viewUrl ? (
            <a className="deposit-v4-action-link" href={selected.receipt.viewUrl}>
              <FileText size={14} /> Generate receipt
            </a>
          ) : (
            <button
              className="deposit-v4-action-link"
              disabled
              title={selected.receipt.disabledReason}
              type="button"
            >
              <FileText size={14} /> Generate receipt
            </button>
          )}
        </section>
      </section>
    </aside>
  );
}

export function OpsDepositsPage() {
  const service = useMemo(() => OpsDepositHoldsFactory.create(), []);
  const [snapshot, setSnapshot] = useState<DepositHoldsSnapshot | null>(null);
  const [selectedId, setSelectedId] = useState(() => new URLSearchParams(window.location.search).get('hold')?.trim() || '');
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.search).get('search')?.trim() || '');
  const [status, setStatus] = useState(() => new URLSearchParams(window.location.search).get('status')?.trim() || '');
  const [page, setPage] = useState(1);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busyAction, setBusyAction] = useState<DepositHoldAction | ''>('');

  useEffect(() => {
    service.loadDeposits()
      .then((nextSnapshot) => {
        setSnapshot(nextSnapshot);
        setSelectedId((current) => (current && nextSnapshot.rows.some((row) => row.id === current) ? current : ''));
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load deposits.'));
  }, [service]);

  const visibleRows = useMemo(() => (
    snapshot ? service.filterDeposits(snapshot.rows, query, status) : []
  ), [query, service, snapshot, status]);
  const pageSize = 8;
  const totalPages = Math.max(1, Math.ceil(visibleRows.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageStart = visibleRows.length ? ((safePage - 1) * pageSize) + 1 : 0;
  const pageEnd = Math.min(safePage * pageSize, visibleRows.length);
  const pagedRows = useMemo(
    () => visibleRows.slice((safePage - 1) * pageSize, safePage * pageSize),
    [safePage, visibleRows],
  );

  useEffect(() => {
    if (page !== safePage) setPage(safePage);
  }, [page, safePage]);

  useEffect(() => {
    if (selectedId && pagedRows.some((row) => row.id === selectedId)) return;
    if (selectedId) setSelectedId('');
  }, [pagedRows, selectedId]);

  const selected = snapshot?.rows.find((row) => row.id === selectedId) || null;

  function toggleSelected(id: string) {
    setSelectedId((current) => (current === id ? '' : id));
  }

  function selectVisibleHold(id: string) {
    const index = visibleRows.findIndex((row) => row.id === id);
    if (index >= 0) setPage(Math.floor(index / pageSize) + 1);
    toggleSelected(id);
  }

  function updateQuery(nextQuery: string) {
    setQuery(nextQuery);
    setPage(1);
  }

  function updateStatus(nextStatus: string) {
    setStatus(nextStatus);
    setPage(1);
  }

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
          <button
            onClick={() => document.getElementById('deposit-status-filter')?.focus()}
            type="button"
          >
            <SlidersHorizontal size={16} /> Filters
          </button>
          <button
            onClick={() => exportDepositLedger(visibleRows)}
            title={`Export ${visibleRows.length} visible deposit holds`}
            type="button"
          >
            <Download size={16} /> Export
          </button>
        </div>
      </section>

      {message && <div className="deposit-v4-alert deposit-v4-alert--success">{message}</div>}
      {error && <div className="deposit-v4-alert deposit-v4-alert--error">{error}</div>}

      <section className="deposit-v4-summary-row">
        <div className="deposit-v4-metric-grid">
          {snapshot.summaryCards.map((metric) => <DepositMetricCard metric={metric} key={metric.label} />)}
        </div>
        <ExpiringSoonPanel holds={snapshot.expiringHolds} onSelect={selectVisibleHold} />
      </section>

      <section className={`deposit-v4-workspace ${selected ? 'deposit-v4-workspace--detail-open' : 'deposit-v4-workspace--no-detail'}`}>
        <DepositsTable
          selectedId={selectedId}
          onSelect={toggleSelected}
          rows={pagedRows}
          totalRows={visibleRows.length}
          page={safePage}
          totalPages={totalPages}
          pageStart={pageStart}
          pageEnd={pageEnd}
          status={status}
          statusOptions={snapshot.statusOptions}
          query={query}
          onQueryChange={updateQuery}
          onStatusChange={updateStatus}
          onPageChange={setPage}
        />
        {selected && (
          <SelectedDepositPanel
            selected={selected}
            onClose={() => setSelectedId('')}
            onAction={applyAction}
            busyAction={busyAction}
          />
        )}
      </section>
    </main>
  );
}
