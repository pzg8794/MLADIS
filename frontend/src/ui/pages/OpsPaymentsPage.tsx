import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  ExternalLink,
  FileText,
  ReceiptText,
  Search,
  X,
} from 'lucide-react';
import { PaymentsFactory } from '../../application/PaymentsFactory';
import type {
  PaymentDetail,
  PaymentFilterOptionPayload,
  PaymentQuickActionPayload,
  PaymentTransaction,
  PaymentsWorkspace,
  PaymentsWorkspaceFilters,
} from '../../domain/payments';
import './ops-payments-page.css';

function PaymentMetricCard({ card }: { card: PaymentsWorkspace['summaryCards'][number] }) {
  return (
    <article className={`payments-object-metric payments-object-metric--${card.tone}`}>
      <span><CreditCard size={18} /></span>
      <p>{card.label}</p>
      <strong>{card.value}</strong>
      <small>{card.trend}</small>
      <svg viewBox="0 0 120 28" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0 20 L14 17 L28 10 L42 18 L56 13 L70 9 L84 12 L98 19 L120 15" />
      </svg>
    </article>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: PaymentFilterOptionPayload[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="payments-object-select">
      <span className="sr-only">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} aria-label={label}>
        <option value="">{label}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label} ({option.count})
          </option>
        ))}
      </select>
    </label>
  );
}

function PaymentTable({
  workspace,
  selectedId,
  filters,
  onFiltersChange,
  onToggle,
}: {
  workspace: PaymentsWorkspace;
  selectedId: string;
  filters: PaymentsWorkspaceFilters;
  onFiltersChange: (filters: PaymentsWorkspaceFilters) => void;
  onToggle: (transaction: PaymentTransaction) => void;
}) {
  const [searchDraft, setSearchDraft] = useState(filters.searchText || '');
  const options = workspace.filterOptions();
  const pagination = workspace.paginationProjection();

  useEffect(() => {
    setSearchDraft(filters.searchText || '');
  }, [filters.searchText]);

  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    onFiltersChange({ ...filters, searchText: searchDraft.trim(), page: 1 });
  };

  const updateFilter = (patch: PaymentsWorkspaceFilters) => {
    onFiltersChange({ ...filters, ...patch, page: 1 });
  };

  return (
    <section className="payments-object-table-card">
      <form className="payments-object-filters" onSubmit={submitSearch}>
        <FilterSelect
          label="All Channels"
          value={filters.channel || ''}
          options={options.channels}
          onChange={(value) => updateFilter({ channel: value })}
        />
        <FilterSelect
          label="All Statuses"
          value={filters.status || ''}
          options={options.statuses}
          onChange={(value) => updateFilter({ status: value })}
        />
        <label className="payments-object-date">
          <span>From</span>
          <input
            type="date"
            value={filters.dateFrom || ''}
            onChange={(event) => updateFilter({ dateFrom: event.target.value })}
          />
        </label>
        <label className="payments-object-date">
          <span>To</span>
          <input
            type="date"
            value={filters.dateTo || ''}
            onChange={(event) => updateFilter({ dateTo: event.target.value })}
          />
        </label>
        <FilterSelect
          label="All Methods"
          value={filters.method || ''}
          options={options.methods}
          onChange={(value) => updateFilter({ method: value })}
        />
        <button className="payments-object-clear" type="button" onClick={() => onFiltersChange({ page: 1, pageSize: filters.pageSize })}>
          Clear filters
        </button>
        <label className="payments-object-search">
          <Search size={14} />
          <input
            aria-label="Search transactions"
            placeholder="Search transactions..."
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
          />
        </label>
        <button type="submit">Search</button>
      </form>
      <table>
        <thead>
          <tr>
            <th aria-label="Select transaction" />
            <th>Transaction ID</th>
            <th>Guest</th>
            <th>Reservation</th>
            <th>Listing</th>
            <th>Channel</th>
            <th>Method</th>
            <th>Date</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Invoice</th>
          </tr>
        </thead>
        <tbody>
          {workspace.transactions.length ? (
            workspace.transactions.map((transaction) => {
              const row = transaction.rowProjection();
              return (
                <tr
                  key={row.id}
                  className={row.id === selectedId ? 'is-selected' : ''}
                  onClick={() => onToggle(transaction)}
                >
                  <td><span className="payments-object-check" /></td>
                  <td><strong>{row.transactionId}</strong></td>
                  <td>{row.guest}</td>
                  <td>{row.reservation}</td>
                  <td>{row.listing}</td>
                  <td>{row.channel}</td>
                  <td>{row.method}</td>
                  <td><span>{row.dateLabel}</span><small>{row.timeLabel}</small></td>
                  <td><strong>{row.amount}</strong></td>
                  <td><span className={`payments-object-status payments-object-status--${row.status.tone}`}>{row.status.label}</span></td>
                  <td>
                    {row.invoiceUrl ? (
                      <a
                        href={row.invoiceUrl}
                        onClick={(event) => event.stopPropagation()}
                        aria-label={`Open invoice ${row.transactionId}`}
                      >
                        <FileText size={16} />
                      </a>
                    ) : (
                      <span title="A live invoice is not available for this sample transaction." aria-label="Invoice unavailable">
                        <FileText size={16} />
                      </span>
                    )}
                  </td>
                </tr>
              );
            })
          ) : (
            <tr>
              <td colSpan={11} className="payments-object-empty-cell">No payment transactions match the current filters.</td>
            </tr>
          )}
        </tbody>
      </table>
      <footer className="payments-object-table-footer">
        <span>Showing {pagination.start} to {pagination.end} of {pagination.total_results} results</span>
        {pagination.total_pages > 1 && (
          <nav aria-label="Payments pagination">
            <button
              type="button"
              disabled={!pagination.has_previous}
              onClick={() => onFiltersChange({ ...filters, page: pagination.previous_page || 1 })}
            >
              <ChevronLeft size={15} />
            </button>
            {(pagination.pages || []).map((page) => (
              <button
                type="button"
                key={page.number}
                className={page.is_current ? 'is-active' : ''}
                onClick={() => onFiltersChange({ ...filters, page: page.number })}
              >
                {page.number}
              </button>
            ))}
            <button
              type="button"
              disabled={!pagination.has_next}
              onClick={() => onFiltersChange({ ...filters, page: pagination.next_page || pagination.page })}
            >
              <ChevronRight size={15} />
            </button>
          </nav>
        )}
      </footer>
    </section>
  );
}

function PaymentActionButton({
  action,
  onAction,
}: {
  action: PaymentQuickActionPayload;
  onAction: (action: PaymentQuickActionPayload) => void;
}) {
  if (action.kind === 'link' && action.url) {
    return (
      <a className={`payments-object-action payments-object-action--${action.tone || 'blue'}`} href={action.url}>
        {action.label}
      </a>
    );
  }
  return (
    <button
      className={`payments-object-action payments-object-action--${action.tone || 'blue'}`}
      type="button"
      disabled={action.kind === 'disabled'}
      title={action.disabled_reason}
      onClick={() => onAction(action)}
    >
      {action.label}
    </button>
  );
}

function PaymentDetailPanel({
  detail,
  onClose,
  onAction,
}: {
  detail: PaymentDetail;
  onClose: () => void;
  onAction: (action: PaymentQuickActionPayload) => void;
}) {
  const invoice = detail.invoiceProjection();
  const status = detail.statusBadgeProjection();
  const reservation = detail.linkedReservationProjection();

  return (
    <aside className="payments-object-detail">
      <header>
        <div>
          <h2>Transaction Details</h2>
          <strong>{invoice.transactionNumber}</strong>
          <small>{invoice.dateLabel} at {invoice.timeLabel}</small>
        </div>
        <button type="button" aria-label="Close payment details" onClick={onClose}><X size={18} /></button>
      </header>

      <section className="payments-object-total">
        <strong>{invoice.amount}</strong>
        <small>Total Paid</small>
        <span className={`payments-object-status payments-object-status--${status.tone}`}>{status.label}</span>
      </section>

      <section className="payments-object-invoice">
        <div className="payments-object-invoice-card">
          <ReceiptText size={26} />
          <strong>MLADIS</strong>
          <span>INVOICE</span>
          <i />
          <i />
          <i />
        </div>
        <div>
          <strong>{invoice.invoiceNumber}</strong>
          <span>Issue date {invoice.issueDate}</span>
          <span>Due date {invoice.dueDate}</span>
          <span>Amount due {invoice.amountDue}</span>
          {invoice.invoiceUrl ? (
            <a href={invoice.invoiceUrl}>View full invoice <ExternalLink size={12} /></a>
          ) : (
            <span title="A live invoice is not available for this transaction.">View full invoice unavailable</span>
          )}
        </div>
      </section>

      <section className="payments-object-linked">
        <h3>Linked Reservation</h3>
        {reservation.view_url ? (
          <a href={reservation.view_url}>{reservation.request_key}</a>
        ) : (
          <span title="This transaction is not linked to a live reservation.">{reservation.request_key}</span>
        )}
        <p>{reservation.listing}</p>
        <small>{reservation.date_range} - Guest: {reservation.guest}</small>
      </section>

      <section className="payments-object-two">
        <div>
          <h3>Deposit History</h3>
          {detail.depositHistoryProjection().map((item) => (
            <p key={`${item.id ?? item.label}-${item.meta}`}>
              {item.view_url ? <a href={item.view_url}><strong>{item.label}</strong></a> : <strong>{item.label}</strong>}
              <span>{item.amount}</span>
              <small>{item.meta} · {item.status}</small>
            </p>
          ))}
        </div>
        <div>
          <h3>Quick Actions</h3>
          {detail.quickActionsProjection().map((action) => (
            <PaymentActionButton key={action.label} action={action} onAction={onAction} />
          ))}
        </div>
      </section>

      <section className="payments-object-timeline">
        <h3>Payment Timeline</h3>
        {detail.timelineProjection().map((item) => (
          <p key={`${item.label}-${item.meta}`}><strong>{item.label}</strong><span>{item.meta}</span></p>
        ))}
      </section>

      <footer>
        <h3>Notes</h3>
        <p>{detail.notesProjection()}</p>
      </footer>
    </aside>
  );
}

export function OpsPaymentsPage() {
  const service = useMemo(() => PaymentsFactory.create(), []);
  const [workspace, setWorkspace] = useState<PaymentsWorkspace | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [filters, setFilters] = useState<PaymentsWorkspaceFilters>({ page: 1, pageSize: 10 });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    service.loadWorkspace(selectedId, filters)
      .then((nextWorkspace) => {
        if (!active) return;
        setWorkspace(nextWorkspace);
        setError('');
      })
      .catch((nextError) => {
        if (!active) return;
        setWorkspace(null);
        setError(nextError instanceof Error ? nextError.message : 'Could not load payments workspace.');
      });
    return () => {
      active = false;
    };
  }, [service, selectedId, filters.searchText, filters.status, filters.channel, filters.method, filters.dateFrom, filters.dateTo, filters.page, filters.pageSize]);

  const applyFilters = (nextFilters: PaymentsWorkspaceFilters) => {
    setFilters(nextFilters);
    setSelectedId('');
    setMessage('');
  };

  const toggleTransaction = (transaction: PaymentTransaction) => {
    setSelectedId((current) => (current === transaction.id ? '' : transaction.id));
    setMessage('');
  };

  const runQuickAction = async (action: PaymentQuickActionPayload) => {
    if (action.kind === 'disabled') {
      setError(action.disabled_reason || 'This action is not currently available.');
      return;
    }
    if (action.kind !== 'post' || !action.action || !selectedId) return;
    try {
      await service.runAction(selectedId, action.action);
      const nextWorkspace = await service.loadWorkspace(selectedId, filters);
      setWorkspace(nextWorkspace);
      setMessage(`${action.label} completed.`);
      setError('');
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : `${action.label} failed.`);
    }
  };

  if (!workspace) {
    return (
      <main className="dashboard-content payments-object-page">
        <p className="payments-object-empty">{error || 'Loading payments workspace...'}</p>
      </main>
    );
  }

  return (
    <main className={`dashboard-content payments-object-page${workspace.selectedDetail ? ' has-detail' : ''}`}>
      <section className="payments-object-titlebar">
        <div>
          <h1>Payments &amp; Transactions</h1>
          <p>Track guest payments, direct-booking invoices, refunds, and reconciled transaction flows.</p>
        </div>
        <div>
          <span className="payments-object-date-label"><CalendarDays size={15} /> {workspace.dateRangeLabel()}</span>
        </div>
      </section>

      {(message || error) && (
        <p className={`payments-object-banner${error ? ' is-error' : ''}`}>{error || message}</p>
      )}

      <section className="payments-object-grid">
        <div className="payments-object-main">
          <section className="payments-object-metrics" aria-label="Payment summary">
            {workspace.metricsProjection().map((card) => (
              <PaymentMetricCard key={card.label} card={card} />
            ))}
          </section>
          <PaymentTable
            workspace={workspace}
            selectedId={selectedId}
            filters={filters}
            onFiltersChange={applyFilters}
            onToggle={toggleTransaction}
          />
        </div>
        {workspace.selectedDetail && (
          <PaymentDetailPanel
            detail={workspace.selectedDetail}
            onClose={() => setSelectedId('')}
            onAction={runQuickAction}
          />
        )}
      </section>
    </main>
  );
}
