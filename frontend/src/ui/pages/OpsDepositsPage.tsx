import { useMemo, useState } from 'react';
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
import './ops-deposits-page.css';

const STAY_IMAGE = `${import.meta.env.BASE_URL}stays/stay-3br.jpg`;

type DepositTone = 'green' | 'orange' | 'blue' | 'red' | 'purple';
type RiskTone = 'low' | 'medium';
type StatusTone = 'on-hold' | 'approved' | 'released' | 'failed' | 'review';

class DepositMetricModel {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly trend: string,
    public readonly icon: LucideIcon,
    public readonly tone: DepositTone,
    public readonly points: string,
  ) {}
}

class DepositRowModel {
  constructor(
    public readonly id: string,
    public readonly guest: string,
    public readonly email: string,
    public readonly initials: string,
    public readonly avatarTone: DepositTone,
    public readonly reservation: string,
    public readonly reservationNumber: string,
    public readonly listing: string,
    public readonly amount: string,
    public readonly requestedDate: string,
    public readonly requestedTime: string,
    public readonly expirationDate: string,
    public readonly expirationTime: string,
    public readonly risk: string,
    public readonly riskTone: RiskTone,
    public readonly status: string,
    public readonly statusTone: StatusTone,
    public readonly hasWarning = false,
  ) {}
}

class ExpiringHoldModel {
  constructor(
    public readonly guest: string,
    public readonly listing: string,
    public readonly timeLeft: string,
  ) {}
}

class TimelineItemModel {
  constructor(
    public readonly title: string,
    public readonly timestamp: string,
    public readonly note: string,
    public readonly tone: DepositTone,
  ) {}
}

const metrics = [
  new DepositMetricModel('Active Holds', '28', '+8 vs last 7 days', BadgeDollarSign, 'green', 'M0 38 L22 34 L44 24 L66 29 L88 26 L110 14 L132 27 L154 31 L176 37 L198 28 L220 32'),
  new DepositMetricModel('Expiring Soon', '7', '+2 vs last 7 days', CalendarClock, 'orange', 'M0 34 L20 28 L39 26 L58 31 L78 30 L98 14 L118 30 L138 33 L158 29 L178 36 L198 33 L220 37'),
  new DepositMetricModel('Released This Week', '36', '+12 vs last 7 days', BadgeCheck, 'blue', 'M0 39 L20 34 L40 25 L60 31 L80 22 L100 28 L120 24 L140 34 L160 32 L180 39 L200 33 L220 34'),
  new DepositMetricModel('Disputes', '2', '-1 vs last 7 days', BadgeAlert, 'red', 'M0 40 L19 36 L38 28 L57 34 L76 39 L95 36 L114 38 L133 31 L152 22 L171 33 L190 37 L220 40'),
];

const expiringHolds = [
  new ExpiringHoldModel('Maria Rodriguez', '3 Beds Apt, Vacation Home & Pool, G-101', '6h 32m'),
  new ExpiringHoldModel('John Smith', '2 Beds Apt, Vacation Home & Pool', '18h 45m'),
  new ExpiringHoldModel('Ana López', 'Meeting Room 1', '1d 4h'),
];

const rows = [
  new DepositRowModel('R-1042', 'Maria Rodriguez', 'maria.rodriguez@email.com', 'MR', 'green', 'R-1042', '#16', '3 Beds Apt, Vacation Home & Pool, G-101', '$200.00', 'Jun 5, 2026', '8:42 PM', 'Jun 7, 2026', '11:59 PM', 'Low', 'low', 'On Hold', 'on-hold'),
  new DepositRowModel('R-1035', 'John Smith', 'john.smith@gmail.com', 'JS', 'blue', 'R-1035', '#7', '2 Beds Apt, Vacation Home & Pool', '$200.00', 'Jun 4, 2026', '10:15 AM', 'Jun 6, 2026', '11:59 PM', 'Low', 'low', 'On Hold', 'on-hold'),
  new DepositRowModel('R-1036', 'Ana López', 'ana.lopez@yahoo.com', 'AL', 'red', 'R-1036', '#9', 'Meeting Room 1', '$250.00', 'Jun 3, 2026', '2:25 PM', 'Jun 5, 2026', '11:59 PM', 'Medium', 'medium', 'Review Needed', 'review', true),
  new DepositRowModel('R-1038', 'David Brown', 'david.brown@outlook.com', 'DL', 'purple', 'R-1038', '#15', '6 Beds Apt, Vacation Home & Pool', '$400.00', 'Jun 2, 2026', '9:08 AM', 'Jun 4, 2026', '11:59 PM', 'Medium', 'medium', 'On Hold', 'on-hold', true),
  new DepositRowModel('R-1040', 'Sophie Martin', 'sophie.martin@gmail.com', 'SM', 'red', 'R-1040', '#13', '3 Beds Apt, Vacation Home & Pool, G-101', '$200.00', 'Jun 1, 2026', '6:34 PM', 'Jun 3, 2026', '11:59 PM', 'Low', 'low', 'Approved', 'approved'),
  new DepositRowModel('R-1031', 'Peter Taylor', 'peter.taylor@gmail.com', 'PT', 'blue', 'R-1031', '#4', '2 Beds Apt, Vacation Home & Pool', '$200.00', 'May 31, 2026', '11:22 AM', 'Jun 2, 2026', '11:59 PM', 'Low', 'low', 'Released', 'released'),
  new DepositRowModel('R-1029', 'Laura Lee', 'laura.lee@yahoo.com', 'LL', 'orange', 'R-1029', '#2', 'Dec lock issue', '$150.00', 'May 30, 2026', '9:41 AM', 'Jun 1, 2026', '11:59 PM', 'Medium', 'medium', 'Failed', 'failed'),
  new DepositRowModel('R-1028', 'Mike Chen', 'mike.chen@gmail.com', 'MC', 'blue', 'R-1028', '#1', 'Conference Room A', '$75.00', 'May 29, 2026', '3:14 PM', 'May 31, 2026', '11:59 PM', 'Low', 'low', 'Released', 'released'),
];

const timeline = [
  new TimelineItemModel('Hold requested', 'Jun 5, 2026 8:42 PM', 'Hold initiated via Stripe', 'blue'),
  new TimelineItemModel('Authorization approved', 'Jun 5, 2026 8:42 PM', 'Approved for $200.00 USD', 'green'),
  new TimelineItemModel('Hold expires', 'Jun 7, 2026 11:59 PM', 'Auto-release unless extended', 'orange'),
];

function DepositSparkline({ metric }: { metric: DepositMetricModel }) {
  return (
    <svg className="deposit-v4-sparkline" viewBox="0 0 220 52" preserveAspectRatio="none" aria-hidden="true">
      <path className="deposit-v4-sparkline__line" d={metric.points} />
    </svg>
  );
}

function DepositMetricCard({ metric }: { metric: DepositMetricModel }) {
  const Icon = metric.icon;
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

function Avatar({ initials, tone }: { initials: string; tone: DepositTone }) {
  return <span className={`deposit-v4-avatar deposit-v4-avatar--${tone}`}>{initials}</span>;
}

function StatusBadge({ label, tone }: { label: string; tone: StatusTone }) {
  return <span className={`deposit-v4-status deposit-v4-status--${tone}`}>{label}</span>;
}

function RiskBadge({ label, tone }: { label: string; tone: RiskTone }) {
  return <span className={`deposit-v4-risk deposit-v4-risk--${tone}`}>{label}</span>;
}

function DepositsTable({ selectedId, onSelect, visibleRows }: { selectedId: string; onSelect: (id: string) => void; visibleRows: DepositRowModel[] }) {
  return (
    <section className="deposit-v4-table-card">
      <div className="deposit-v4-table-toolbar">
        <label className="deposit-v4-search">
          <Search size={15} />
          <input aria-label="Search deposits" placeholder="Search by guest name, email, reservation #..." readOnly />
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
                  <button className={`deposit-v4-check ${row.id === selectedId ? 'is-checked' : ''}`} type="button" aria-label={`Select ${row.guest}`}>
                    {row.id === selectedId && <CheckCircle2 size={13} />}
                  </button>
                </td>
                <td>
                  <div className="deposit-v4-guest-cell">
                    <Avatar initials={row.initials} tone={row.avatarTone} />
                    <span><strong>{row.guest}</strong><small>{row.email}</small></span>
                  </div>
                </td>
                <td><strong>{row.reservation}</strong><small>{row.reservationNumber}</small></td>
                <td>{row.listing}</td>
                <td><strong>{row.amount}</strong><small>USD</small></td>
                <td>{row.requestedDate}<small>{row.requestedTime}</small></td>
                <td>{row.expirationDate}<small>{row.expirationTime}</small>{row.hasWarning && <i className="deposit-v4-warning">!</i>}</td>
                <td><RiskBadge label={row.risk} tone={row.riskTone} /></td>
                <td><StatusBadge label={row.status} tone={row.statusTone} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer className="deposit-v4-table-footer">
        <span>Showing 1 to 8 of 28 results</span>
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

function ExpiringSoonPanel() {
  return (
    <section className="deposit-v4-expiring">
      <header>
        <h2><Clock3 size={17} /> Expiring Soon</h2>
        <a href="/ops/deposits/">View all (7)</a>
      </header>
      <div>
        {expiringHolds.map((item) => (
          <article key={item.guest}>
            <i />
            <span><strong>{item.guest}</strong><small>{item.listing}</small></span>
            <em>{item.timeLeft}</em>
          </article>
        ))}
      </div>
    </section>
  );
}

function SelectedDepositPanel({ selected }: { selected: DepositRowModel }) {
  return (
    <aside className="deposit-v4-detail">
      <section className="deposit-v4-person-card">
        <button className="deposit-v4-close" type="button" aria-label="Close selected deposit"><X size={17} /></button>
        <div className="deposit-v4-person-head">
          <Avatar initials="MR" tone="green" />
          <div>
            <h2>{selected.guest}</h2>
            <p>{selected.email}</p>
            <span><Phone size={13} /> +1 (809) 555-0169 <b>Repeat guest</b></span>
          </div>
        </div>

        <article className="deposit-v4-reservation-card">
          <img src={STAY_IMAGE} alt="3 Beds Apt, Vacation Home & Pool, G-101" />
          <div>
            <small>Reservation <strong>R-1042</strong></small>
            <h3>3 Beds Apt, Vacation Home &amp; Pool, G-101</h3>
            <p>Sun, Jun 8 – Jun 14, 2026 • 6 nights</p>
          </div>
        </article>

        <section className="deposit-v4-hold-facts">
          <div><small>Hold Amount</small><strong>$200.00 USD</strong><StatusBadge label="On Hold" tone="on-hold" /></div>
          <div><small>Requested</small><span>Jun 5, 2026 at 8:42 PM</span></div>
          <div><small>Expires</small><span>Jun 7, 2026 at 11:59 PM <em>(in 6h 32m)</em></span></div>
        </section>

        <section className="deposit-v4-timeline">
          <h3>Authorization Timeline</h3>
          <ol>
            {timeline.map((item) => (
              <li className={`deposit-v4-tone--${item.tone}`} key={item.title}>
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
          <article>
            <span className="deposit-v4-card-brand">VISA</span>
            <div><strong>•••• 4242</strong><StatusBadge label="Approved" tone="approved" /></div>
            <time>Jun 5, 2026 8:42 PM</time>
            <small>Auth ID: auth_1N8g... <b>$200.00 USD</b></small>
          </article>
        </section>

        <section className="deposit-v4-note">
          <h3>Guest Note</h3>
          <p>Will arrive late evening. Please hold the deposit.</p>
        </section>

        <section className="deposit-v4-actions">
          <button className="deposit-v4-primary" type="button">Approve hold</button>
          <div>
            <button type="button">Release hold</button>
            <button type="button">Request guest action</button>
          </div>
          <button type="button"><FileText size={14} /> Generate receipt</button>
        </section>
      </section>
    </aside>
  );
}

export function OpsDepositsPage() {
  const [selectedId, setSelectedId] = useState('R-1042');
  const [query] = useState('');

  const visibleRows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return rows;
    return rows.filter((row) => [row.guest, row.email, row.reservation, row.listing].some((value) => value.toLowerCase().includes(normalizedQuery)));
  }, [query]);

  const selected = rows.find((row) => row.id === selectedId) || rows[0];

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

      <section className="deposit-v4-summary-row">
        <div className="deposit-v4-metric-grid">
          {metrics.map((metric) => <DepositMetricCard metric={metric} key={metric.label} />)}
        </div>
        <ExpiringSoonPanel />
      </section>

      <section className="deposit-v4-workspace">
        <DepositsTable selectedId={selectedId} onSelect={setSelectedId} visibleRows={visibleRows} />
        <SelectedDepositPanel selected={selected} />
      </section>
    </main>
  );
}
