import { useEffect, useMemo, useState } from 'react';
import {
  CalendarDays,
  ChevronDown,
  CreditCard,
  Download,
  FileText,
  Filter,
  MoreVertical,
  ReceiptText,
  Search,
  X,
} from 'lucide-react';
import { PaymentsFactory } from '../../application/PaymentsFactory';
import type { PaymentDetail, PaymentTransaction, PaymentsWorkspace } from '../../domain/payments';
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

function PaymentTable({
  transactions,
  selectedId,
  onToggle,
}: {
  transactions: PaymentTransaction[];
  selectedId: string;
  onToggle: (transaction: PaymentTransaction) => void;
}) {
  return (
    <section className="payments-object-table-card">
      <header className="payments-object-filters">
        <button type="button">All Channels <ChevronDown size={14} /></button>
        <button type="button">All Statuses <ChevronDown size={14} /></button>
        <button type="button"><CalendarDays size={14} /> Jun 6, 2026 - Jun 12, 2026</button>
        <button type="button">All Methods <ChevronDown size={14} /></button>
        <label>
          <Search size={14} />
          <input aria-label="Search transactions" placeholder="Search transactions..." readOnly />
        </label>
      </header>
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
          {transactions.map((transaction) => (
            <tr
              key={transaction.id}
              className={transaction.id === selectedId ? 'is-selected' : ''}
              onClick={() => onToggle(transaction)}
            >
              <td><span className="payments-object-check" /></td>
              <td><strong>{transaction.transactionId}</strong></td>
              <td>{transaction.guest}</td>
              <td>{transaction.reservation}</td>
              <td>{transaction.listing}</td>
              <td>{transaction.channel}</td>
              <td>{transaction.method}</td>
              <td><span>{transaction.dateLabel}</span><small>{transaction.timeLabel}</small></td>
              <td><strong>{transaction.amount}</strong></td>
              <td><span className={`payments-object-status payments-object-status--${transaction.statusTone}`}>{transaction.status}</span></td>
              <td><FileText size={16} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function PaymentDetailPanel({ detail, onClose }: { detail: PaymentDetail; onClose: () => void }) {
  const data = detail.payload;

  return (
    <aside className="payments-object-detail">
      <header>
        <div>
          <h2>Transaction Details</h2>
          <strong>{data.transaction_id}</strong>
          <small>{data.date_label} at {data.time_label}</small>
        </div>
        <button type="button" aria-label="Close payment details" onClick={onClose}><X size={18} /></button>
      </header>

      <section className="payments-object-total">
        <strong>{data.amount} <span>USD</span></strong>
        <small>Total Paid</small>
        <span className={`payments-object-status payments-object-status--${data.status_cls}`}>{data.status}</span>
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
          <strong>{data.invoice_number}</strong>
          <span>Issue date {data.issue_date}</span>
          <span>Due date {data.due_date}</span>
          <span>Amount due {data.amount_due}</span>
        </div>
      </section>

      <section className="payments-object-linked">
        <h3>Linked Reservation</h3>
        <a href={data.linked_reservation.url}>{data.linked_reservation.request_key}</a>
        <p>{data.linked_reservation.listing}</p>
        <small>{data.linked_reservation.date_range} - Guest: {data.linked_reservation.guest}</small>
      </section>

      <section className="payments-object-two">
        <div>
          <h3>Deposit History</h3>
          {data.deposit_history.map((item) => (
            <p key={item.label}><strong>{item.label}</strong><span>{item.amount}</span><small>{item.meta}</small></p>
          ))}
        </div>
        <div>
          <h3>Quick Actions</h3>
          {data.quick_actions.map((action) => (
            <button type="button" disabled={action.kind === 'disabled'} key={action.label}>
              {action.label}
            </button>
          ))}
        </div>
      </section>

      <section className="payments-object-timeline">
        <h3>Payment Timeline</h3>
        {data.timeline.map((item) => (
          <p key={item.label}><strong>{item.label}</strong><span>{item.meta}</span></p>
        ))}
      </section>

      <footer>
        <h3>Notes</h3>
        <p>{data.notes}</p>
      </footer>
    </aside>
  );
}

export function OpsPaymentsPage() {
  const service = useMemo(() => PaymentsFactory.create(), []);
  const [workspace, setWorkspace] = useState<PaymentsWorkspace | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [detail, setDetail] = useState<PaymentDetail | null>(null);

  useEffect(() => {
    let active = true;
    service.loadWorkspace()
      .then((nextWorkspace) => {
        if (!active) return;
        setWorkspace(nextWorkspace);
      })
      .catch(() => {
        if (active) setWorkspace(null);
      });
    return () => {
      active = false;
    };
  }, [service]);

  const toggleTransaction = (transaction: PaymentTransaction) => {
    if (selectedId === transaction.id) {
      setSelectedId('');
      setDetail(null);
      return;
    }

    setSelectedId(transaction.id);
    service.loadWorkspace(transaction.id)
      .then((nextWorkspace) => {
        setWorkspace(nextWorkspace);
        setDetail(nextWorkspace.selectedDetail);
      })
      .catch(() => setDetail(null));
  };

  if (!workspace) {
    return (
      <main className="dashboard-content payments-object-page">
        <p className="payments-object-empty">Loading payments workspace...</p>
      </main>
    );
  }

  return (
    <main className={`dashboard-content payments-object-page${detail ? ' has-detail' : ''}`}>
      <section className="payments-object-titlebar">
        <div>
          <h1>Payments &amp; Transactions</h1>
          <p>Track guest payments, direct-booking invoices, refunds, and reconciled transaction flows.</p>
        </div>
        <div>
          <button type="button"><CalendarDays size={16} /> Jun 6 - Jun 12, 2026 <ChevronDown size={15} /></button>
          <button type="button"><Filter size={16} /> Filters</button>
          <button type="button"><Download size={16} /> Export</button>
          <button type="button" aria-label="More payment actions"><MoreVertical size={17} /></button>
        </div>
      </section>

      <section className="payments-object-grid">
        <div className="payments-object-main">
          <section className="payments-object-metrics" aria-label="Payment summary">
            {workspace.summaryCards.map((card) => (
              <PaymentMetricCard key={card.label} card={card} />
            ))}
          </section>
          <PaymentTable transactions={workspace.transactions} selectedId={selectedId} onToggle={toggleTransaction} />
        </div>
        {detail && <PaymentDetailPanel detail={detail} onClose={() => { setSelectedId(''); setDetail(null); }} />}
      </section>
    </main>
  );
}
