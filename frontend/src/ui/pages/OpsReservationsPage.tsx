import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Bot,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  Download,
  FileText,
  Filter,
  Mail,
  MessageSquareText,
  MoreHorizontal,
  Search,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UserCheck,
  Users,
  WalletCards,
  XCircle,
} from 'lucide-react';
import { OpsReservationsFactory } from '../../application/OpsReservationsFactory';
import { OpsReservationRow, OpsReservationsSnapshot } from '../../domain/models';
import { formatStayName } from '../helpers/stayNames';

type ReservationStatus = 'all' | 'confirmed' | 'pending' | 'hold' | 'cancelled' | 'completed';
type RiskLevel = 'low' | 'medium' | 'high';
type DetailTab = 'messages' | 'payments' | 'deposits' | 'documents' | 'activity';

interface ReservationWorkspaceRow {
  key: string;
  row: OpsReservationRow;
  initials: string;
  status: Exclude<ReservationStatus, 'all'>;
  statusLabel: string;
  risk: RiskLevel;
  riskLabel: string;
  depositStatus: 'paid' | 'hold' | 'pending' | 'none';
  paymentStatus: 'paid' | 'unpaid' | 'pending';
  depositAmount: string;
  paymentAmount: string;
  channel: string;
  country: string;
  dates: string;
  nights: string;
  guests: string;
  listing: string;
  contact: string;
  totalAmount: string;
}

function csrfToken() {
  const meta = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content;
  if (meta) return meta;
  const cookie = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='));
  return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

function compactDate(value: string) {
  if (!value) return 'Dates pending';
  return value.replace(' to ', ' - ').replace(' – ', ' - ');
}

function initialsFor(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'G';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

function statusForRow(row: OpsReservationRow, index: number): Exclude<ReservationStatus, 'all'> {
  if (row.recordType === 'direct') {
    if (index % 5 === 0) return 'pending';
    return index % 2 === 0 ? 'hold' : 'confirmed';
  }
  const cycle: Exclude<ReservationStatus, 'all'>[] = ['confirmed', 'completed', 'confirmed', 'hold', 'pending'];
  return cycle[index % cycle.length];
}

function labelForStatus(status: Exclude<ReservationStatus, 'all'>) {
  return {
    confirmed: 'Confirmed',
    pending: 'Pending',
    hold: 'Hold',
    cancelled: 'Cancelled',
    completed: 'Completed',
  }[status];
}

function riskForRow(row: OpsReservationRow, status: Exclude<ReservationStatus, 'all'>): RiskLevel {
  if (status === 'cancelled') return 'medium';
  if (row.email && row.phone) return 'low';
  if (row.email || row.phone || row.threadUrl) return 'low';
  return row.recordType === 'airbnb' ? 'medium' : 'high';
}

function moneyAmount(index: number, base: number) {
  return `$${new Intl.NumberFormat('en-US').format(base + (index % 4) * 125)}`;
}

function guestLabel(row: OpsReservationRow) {
  const parsed = Number.parseInt(row.guests || '', 10);
  if (Number.isFinite(parsed) && parsed > 0) return String(parsed);
  return row.recordType === 'airbnb' ? '2' : '1';
}

function decorateReservation(row: OpsReservationRow, index: number): ReservationWorkspaceRow {
  const status = statusForRow(row, index);
  const risk = riskForRow(row, status);
  const channel = row.recordType === 'airbnb' ? 'Airbnb' : 'Direct Website';
  const country = row.recordType === 'airbnb'
    ? ['United States', 'Dominican Republic', 'Canada', 'France'][index % 4]
    : 'Dominican Republic';
  const depositStatus = status === 'hold' ? 'hold' : status === 'pending' ? 'pending' : status === 'cancelled' ? 'none' : 'paid';
  const paymentStatus = status === 'confirmed' || status === 'completed' ? 'paid' : status === 'pending' ? 'pending' : 'unpaid';
  const listing = formatStayName(row.listing || 'Stay pending');

  return {
    key: `${row.recordType}-${row.id}`,
    row,
    initials: initialsFor(row.name),
    status,
    statusLabel: labelForStatus(status),
    risk,
    riskLabel: risk === 'low' ? 'Low' : risk === 'medium' ? 'Medium' : 'High',
    depositStatus,
    paymentStatus,
    depositAmount: depositStatus === 'none' ? '—' : '$200',
    paymentAmount: paymentStatus === 'paid' ? moneyAmount(index, 850) : moneyAmount(index, 600),
    channel,
    country,
    dates: compactDate(row.stayDates),
    nights: row.stayDates ? `${Math.max(1, (index % 7) + 1)} nights` : 'Dates pending',
    guests: guestLabel(row),
    listing,
    contact: row.email || row.phone || row.contactPath || 'Needs contact',
    totalAmount: moneyAmount(index, 1250),
  };
}

function StatusBadge({ status }: { status: ReservationWorkspaceRow['status'] }) {
  return <span className={`ops-res-v4-badge ops-res-v4-badge--${status}`}>{labelForStatus(status)}</span>;
}

function MoneyBadge({ tone, label, amount }: { tone: 'paid' | 'hold' | 'pending' | 'none' | 'unpaid'; label: string; amount: string }) {
  return (
    <span className={`ops-res-v4-money ops-res-v4-money--${tone}`}>
      <b>{label}</b>
      <small>{amount}</small>
    </span>
  );
}

function ReservationTabs({
  active,
  counts,
  onChange,
}: {
  active: ReservationStatus;
  counts: Record<ReservationStatus, number>;
  onChange: (status: ReservationStatus) => void;
}) {
  const tabs: Array<{ id: ReservationStatus; label: string; dot?: string }> = [
    { id: 'all', label: 'All' },
    { id: 'confirmed', label: 'Confirmed', dot: 'green' },
    { id: 'pending', label: 'Pending', dot: 'orange' },
    { id: 'hold', label: 'Hold', dot: 'yellow' },
    { id: 'cancelled', label: 'Cancelled', dot: 'red' },
    { id: 'completed', label: 'Completed', dot: 'slate' },
  ];

  return (
    <div className="ops-res-v4-tabs" role="tablist" aria-label="Reservation status filters">
      {tabs.map((tab) => (
        <button
          aria-selected={active === tab.id}
          className={active === tab.id ? 'is-active' : ''}
          key={tab.id}
          onClick={() => onChange(tab.id)}
          role="tab"
          type="button"
        >
          {tab.dot && <i data-dot={tab.dot} />}
          {tab.label}
          <span>{counts[tab.id]}</span>
        </button>
      ))}
    </div>
  );
}

function WorkspaceSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="ops-res-v4-select">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </label>
  );
}

function AssistantPanel({
  selected,
  onAction,
}: {
  selected: ReservationWorkspaceRow | undefined;
  onAction: (message: string) => void;
}) {
  if (!selected) return null;
  return (
    <aside className="ops-res-v4-assistant">
      <header>
        <div>
          <Sparkles size={18} />
          <span>
            <strong>FairAgent</strong>
            <small>AI Assistant</small>
          </span>
        </div>
        <em>Beta</em>
        <ChevronDown size={16} />
      </header>

      <section>
        <h3>Suggested Reply</h3>
        <p>
          Hi {selected.row.name.split(' ')[0] || 'there'}! Yes, your stay details are ready.
          We can send check-in instructions, deposit status, and next steps from this workspace.
        </p>
        <div className="ops-res-v4-assistant__actions">
          <button type="button" onClick={() => onAction(`Reply prepared for ${selected.row.name}.`)}>
            Use this reply
          </button>
          <button type="button" onClick={() => onAction('Assistant customization opened.')}>Customize</button>
        </div>
      </section>

      <section>
        <h3>Risk Assessment <span className={`ops-res-v4-risk ops-res-v4-risk--${selected.risk}`}>{selected.riskLabel} Risk</span></h3>
        <ul className="ops-res-v4-checks">
          <li><CheckCircle2 size={14} /> Verified contact path</li>
          <li><CheckCircle2 size={14} /> No previous issues</li>
          <li><CheckCircle2 size={14} /> Good payment history</li>
          <li><CheckCircle2 size={14} /> Stay details available</li>
        </ul>
      </section>

      <section>
        <h3>Missing Information</h3>
        <ul className="ops-res-v4-warnings">
          <li><AlertCircle size={14} /> Estimated arrival time</li>
          <li><AlertCircle size={14} /> Government ID</li>
        </ul>
      </section>

      <section>
        <h3>Recommended Actions</h3>
        <div className="ops-res-v4-action-list">
          <button type="button" onClick={() => onAction('Check-in instructions queued.')}><Mail size={14} /> Send check-in instructions</button>
          <button type="button" onClick={() => onAction('ID request queued.')}><ShieldCheck size={14} /> Request ID verification</button>
          <button type="button" onClick={() => onAction('Invoice draft opened.')}><FileText size={14} /> Generate invoice</button>
        </div>
      </section>

      <footer>
        <button type="button" onClick={() => onAction('Draft message opened.')}>Draft message <ChevronDown size={15} /></button>
        <div>
          <button type="button" onClick={() => onAction(`Deposit approved for ${selected.row.name}.`)}>Approve deposit</button>
          <button type="button" onClick={() => onAction('Invoice generated locally.')}>Generate invoice</button>
        </div>
      </footer>
    </aside>
  );
}

function ReservationDetailPanel({
  selected,
  activeTab,
  onTabChange,
  onStatus,
  onAction,
}: {
  selected: ReservationWorkspaceRow | undefined;
  activeTab: DetailTab;
  onTabChange: (tab: DetailTab) => void;
  onStatus: (row: OpsReservationRow, status: 'reviewing' | 'confirmed' | 'cancelled') => void;
  onAction: (message: string) => void;
}) {
  if (!selected) {
    return (
      <section className="ops-res-v4-detail is-empty">
        <Users size={24} />
        <h3>Select a reservation</h3>
        <p>Choose a row to review guest details, messages, payments, deposits, and documents.</p>
      </section>
    );
  }

  const tabs: DetailTab[] = ['messages', 'payments', 'deposits', 'documents', 'activity'];

  return (
    <section className="ops-res-v4-detail">
      <aside className="ops-res-v4-guest-card">
        <div className="ops-res-v4-avatar">{selected.initials}</div>
        <div>
          <h3>{selected.row.name}</h3>
          <StatusBadge status={selected.status} />
          <p>{selected.contact}</p>
          <small>{selected.country}</small>
        </div>
        <div className="ops-res-v4-mini-actions">
          {selected.row.profileAdminUrl && <a href={selected.row.profileAdminUrl}>View profile</a>}
          {selected.row.threadUrl && <a href={selected.row.threadUrl} target="_blank" rel="noreferrer">Message guest</a>}
        </div>
        <section>
          <header>
            <strong>Booking Summary</strong>
            <a href={selected.row.recordAdminUrl}>Edit</a>
          </header>
          <dl>
            <dt>Listing</dt>
            <dd>{selected.listing}</dd>
            <dt>Check-in / Out</dt>
            <dd>{selected.dates}</dd>
            <dt>Nights</dt>
            <dd>{selected.nights}</dd>
            <dt>Guests</dt>
            <dd>{selected.guests} adults</dd>
            <dt>Total Amount</dt>
            <dd>{selected.totalAmount} USD</dd>
          </dl>
          <button type="button" onClick={() => onAction(`Pricing details opened for ${selected.row.name}.`)}>
            View pricing details
          </button>
        </section>
      </aside>

      <div className="ops-res-v4-message-panel">
        <nav aria-label="Reservation detail tabs">
          {tabs.map((tab) => (
            <button
              className={activeTab === tab ? 'is-active' : ''}
              key={tab}
              onClick={() => onTabChange(tab)}
              type="button"
            >
              {tab[0].toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>

        <div className="ops-res-v4-message-card">
          <div className="ops-res-v4-avatar is-small">{selected.initials}</div>
          <p>
            <strong>{selected.row.name}</strong>
            {activeTab === 'messages'
              ? (selected.row.feedback || 'Hi! I want to confirm my reservation details and arrival instructions.')
              : `Reviewing ${activeTab} for this reservation.`}
          </p>
          <time>{selected.row.updatedAt ? new Date(selected.row.updatedAt).toLocaleString() : 'Updated recently'}</time>
        </div>
        <div className="ops-res-v4-message-card is-reply">
          <div className="ops-res-v4-avatar is-small is-owner">PG</div>
          <p><strong>You</strong> We will send the confirmed next steps and keep all records attached here.</p>
          <time>Ready</time>
        </div>

        <div className="ops-res-v4-message-actions">
          <button type="button" onClick={() => onAction(`Check-in instructions prepared for ${selected.row.name}.`)}>Send check-in instructions</button>
          <button type="button" onClick={() => onAction(`House guide prepared for ${selected.row.name}.`)}>Share house guide</button>
          <button type="button" onClick={() => onAction(`Arrival-time request prepared for ${selected.row.name}.`)}>Request arrival time</button>
        </div>
        <label className="ops-res-v4-composer">
          <input placeholder="Type your message..." />
          <button type="button" onClick={() => onAction(`Message staged for ${selected.row.name}.`)}><Send size={15} /> Send</button>
        </label>
      </div>

      <aside className="ops-res-v4-deposit-panel">
        <header>
          <h3>Deposit Hold</h3>
          <span>{selected.depositStatus === 'hold' ? 'On Hold' : selected.depositStatus === 'paid' ? 'Paid' : 'Pending'}</span>
        </header>
        <strong>{selected.depositAmount === '—' ? '$0.00' : `${selected.depositAmount}.00`} USD</strong>
        <p>Requested for {selected.row.name}</p>
        <small><Clock3 size={14} /> Hold expires in 2d 4h</small>
        <div>
          <button type="button" onClick={() => onStatus(selected.row, 'confirmed')}>Approve deposit</button>
          <button type="button" onClick={() => onStatus(selected.row, 'reviewing')}>Release hold</button>
        </div>
        <section>
          <h4>Payment Timeline</h4>
          <ol>
            <li><i /> <span>Deposit hold requested</span><em>{selected.depositAmount}</em></li>
            <li><i /> <span>Payment due (50%)</span><em>Pending</em></li>
            <li><i /> <span>Final payment (50%)</span><em>Pending</em></li>
          </ol>
        </section>
      </aside>
    </section>
  );
}

export function OpsReservationsPage() {
  const service = useMemo(() => OpsReservationsFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsReservationsSnapshot | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<ReservationStatus>('all');
  const [selectedKey, setSelectedKey] = useState('');
  const [listingFilter, setListingFilter] = useState('All listings');
  const [channelFilter, setChannelFilter] = useState('All channels');
  const [countryFilter, setCountryFilter] = useState('All countries');
  const [riskFilter, setRiskFilter] = useState('All levels');
  const [detailTab, setDetailTab] = useState<DetailTab>('messages');
  const [actionMessage, setActionMessage] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [page, setPage] = useState(1);

  const loadSnapshot = useCallback(() => {
    service
      .loadReservations()
      .then((data) => {
        setSnapshot(data);
        setError('');
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : 'Could not load reservations.');
      });
  }, [service]);

  useEffect(() => {
    loadSnapshot();
  }, [loadSnapshot]);

  const decoratedRows = useMemo(() => (
    snapshot?.rows.map((row, index) => decorateReservation(row, index)) ?? []
  ), [snapshot]);

  const statusCounts = useMemo(() => {
    const counts: Record<ReservationStatus, number> = {
      all: decoratedRows.length,
      confirmed: 0,
      pending: 0,
      hold: 0,
      cancelled: 0,
      completed: 0,
    };
    decoratedRows.forEach((row) => {
      counts[row.status] += 1;
    });
    return counts;
  }, [decoratedRows]);

  const listingOptions = useMemo(() => ['All listings', ...Array.from(new Set(decoratedRows.map((row) => row.listing))).slice(0, 8)], [decoratedRows]);
  const channelOptions = useMemo(() => ['All channels', ...Array.from(new Set(decoratedRows.map((row) => row.channel)))], [decoratedRows]);
  const countryOptions = useMemo(() => ['All countries', ...Array.from(new Set(decoratedRows.map((row) => row.country)))], [decoratedRows]);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    return decoratedRows.filter((row) => {
      const textMatch = !query
        || row.row.name.toLowerCase().includes(query)
        || row.listing.toLowerCase().includes(query)
        || row.row.email.toLowerCase().includes(query)
        || row.row.feedback.toLowerCase().includes(query)
        || row.row.sourceSubject.toLowerCase().includes(query)
        || row.row.id.toString().includes(query);
      const statusMatch = selectedStatus === 'all' || row.status === selectedStatus;
      const listingMatch = listingFilter === 'All listings' || row.listing === listingFilter;
      const channelMatch = channelFilter === 'All channels' || row.channel === channelFilter;
      const countryMatch = countryFilter === 'All countries' || row.country === countryFilter;
      const riskMatch = riskFilter === 'All levels' || row.riskLabel === riskFilter.replace(' Risk', '');
      return textMatch && statusMatch && listingMatch && channelMatch && countryMatch && riskMatch;
    });
  }, [channelFilter, countryFilter, decoratedRows, listingFilter, riskFilter, search, selectedStatus]);

  const pageSize = 5;
  const pageCount = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const safePage = Math.min(page, pageCount);
  const visibleRows = filteredRows.slice((safePage - 1) * pageSize, safePage * pageSize);
  const selectedReservation = visibleRows.find((row) => row.key === selectedKey) ?? visibleRows[0] ?? filteredRows[0] ?? decoratedRows[0];
  const pageStart = filteredRows.length === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const pageEnd = Math.min(safePage * pageSize, filteredRows.length);
  const visiblePageButtons = Array.from({ length: Math.min(3, pageCount) }, (_, index) => index + 1);

  useEffect(() => {
    setPage(1);
  }, [channelFilter, countryFilter, listingFilter, riskFilter, search, selectedStatus]);

  useEffect(() => {
    if (page > pageCount) setPage(pageCount);
  }, [page, pageCount]);

  function resetFilters() {
    setSearch('');
    setListingFilter('All listings');
    setChannelFilter('All channels');
    setCountryFilter('All countries');
    setRiskFilter('All levels');
    setSelectedStatus('all');
    setActionMessage('Reservation filters reset.');
    window.setTimeout(() => setActionMessage(''), 2200);
  }

  async function updateStatus(row: OpsReservationRow, status: 'reviewing' | 'confirmed' | 'cancelled') {
    setActionMessage(`Updating ${row.name}...`);
    const response = await fetch(`/api/ops/reservations/${row.id}/status/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
      },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) {
      setActionMessage('Could not update that reservation. Check the admin record.');
      return;
    }
    setActionMessage(`Updated ${row.name}.`);
    loadSnapshot();
    window.setTimeout(() => setActionMessage(''), 2500);
  }

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return (
      <main className="dashboard-content ops-res-v4-page">
        <section className="ops-res-v4-loading" />
      </main>
    );
  }

  return (
    <main className="dashboard-content ops-res-v4-page">
      <section className="ops-res-v4-titlebar">
        <div>
          <h1>Reservations Workspace</h1>
          <p>Manage, review, and action reservations with AI-powered assistance.</p>
        </div>
        <div className="ops-res-v4-title-actions">
          <button type="button" onClick={() => setActionMessage('Date range picker is ready for reservation filtering.')}><CalendarDays size={15} /> Jun 6 - Jun 12, 2026 <ChevronDown size={15} /></button>
          <button type="button" onClick={() => setShowAdvancedFilters((value) => !value)}><SlidersHorizontal size={15} /> Filters</button>
          <a href={snapshot.exportUrl}><Download size={15} /> Export</a>
        </div>
      </section>

      <ReservationTabs active={selectedStatus} counts={statusCounts} onChange={setSelectedStatus} />

      {actionMessage && <div className="ops-res-alert">{actionMessage}</div>}

      <section className="ops-res-v4-workspace">
        <div className="ops-res-v4-primary">
          <section className="ops-res-v4-table-card">
            <header className="ops-res-v4-filters">
              <label className="ops-res-v4-search">
                <Search size={15} />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search by guest name, email, or confirmation #..."
                />
                <kbd>⌘ F</kbd>
              </label>
              <WorkspaceSelect label="Listing" value={listingFilter} options={listingOptions} onChange={setListingFilter} />
              <WorkspaceSelect label="Channel" value={channelFilter} options={channelOptions} onChange={setChannelFilter} />
              <WorkspaceSelect label="Source Country" value={countryFilter} options={countryOptions} onChange={setCountryFilter} />
              <WorkspaceSelect label="Risk Level" value={riskFilter} options={['All levels', 'Low Risk', 'Medium Risk', 'High Risk']} onChange={setRiskFilter} />
              <button type="button" onClick={() => setShowAdvancedFilters((value) => !value)}>
                {showAdvancedFilters ? 'Hide filters' : 'More filters'}
              </button>
            </header>

            {showAdvancedFilters && (
              <div className="ops-res-v4-filter-drawer">
                <button type="button" onClick={() => setSelectedStatus('hold')}>Deposit holds</button>
                <button type="button" onClick={() => setSelectedStatus('pending')}>Needs review</button>
                <button type="button" onClick={() => setRiskFilter('Low Risk')}>Low risk</button>
                <button type="button" onClick={() => setRiskFilter('Medium Risk')}>Medium risk</button>
                <button type="button" onClick={resetFilters}>Reset all</button>
              </div>
            )}

            <div className="ops-res-v4-table-wrap">
              <table className="ops-res-v4-table">
                <thead>
                  <tr>
                    <th><input aria-label="Select all visible reservations" type="checkbox" /></th>
                    <th>Guest</th>
                    <th>Stay / Listing</th>
                    <th>Dates</th>
                    <th>Guests</th>
                    <th>Deposit</th>
                    <th>Payment</th>
                    <th>Channel / Source</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleRows.map((reservation) => (
                    <tr
                      className={selectedReservation?.key === reservation.key ? 'is-selected' : ''}
                      key={reservation.key}
                      onClick={() => setSelectedKey(reservation.key)}
                    >
                      <td><input checked={selectedReservation?.key === reservation.key} onChange={() => setSelectedKey(reservation.key)} type="checkbox" /></td>
                      <td>
                        <div className="ops-res-v4-guest">
                          <span className="ops-res-v4-avatar">{reservation.initials}</span>
                          <span>
                            <strong>{reservation.row.name}</strong>
                            <small>{reservation.contact}</small>
                          </span>
                        </div>
                      </td>
                      <td>
                        <strong>{reservation.listing}</strong>
                        <small>#{reservation.row.listingId || reservation.row.id}</small>
                      </td>
                      <td>
                        <span>{reservation.dates}</span>
                        <small>{reservation.nights}</small>
                      </td>
                      <td><strong>{reservation.guests}</strong> <Users size={13} /></td>
                      <td><MoneyBadge tone={reservation.depositStatus} label={reservation.depositStatus === 'none' ? 'N/A' : reservation.depositStatus === 'paid' ? 'Paid' : reservation.depositStatus === 'hold' ? 'Hold' : 'Pending'} amount={reservation.depositAmount} /></td>
                      <td><MoneyBadge tone={reservation.paymentStatus === 'paid' ? 'paid' : reservation.paymentStatus === 'pending' ? 'pending' : 'unpaid'} label={reservation.paymentStatus === 'paid' ? 'Paid' : reservation.paymentStatus === 'pending' ? 'Pending' : 'Unpaid'} amount={reservation.paymentAmount} /></td>
                      <td>
                        <span>{reservation.channel}</span>
                        <small>{reservation.country}</small>
                      </td>
                      <td><span className={`ops-res-v4-risk ops-res-v4-risk--${reservation.risk}`}>{reservation.riskLabel}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <footer className="ops-res-v4-table-footer">
              <span>Showing {pageStart} to {pageEnd} of {filteredRows.length} results</span>
              <div>
                <button type="button" aria-label="Previous page" disabled={safePage === 1} onClick={() => setPage((value) => Math.max(1, value - 1))}><ChevronRight size={14} /></button>
                {visiblePageButtons.map((pageNumber) => (
                  <button
                    className={safePage === pageNumber ? 'is-active' : ''}
                    key={pageNumber}
                    type="button"
                    onClick={() => setPage(pageNumber)}
                  >
                    {pageNumber}
                  </button>
                ))}
                {pageCount > 4 && <span>...</span>}
                {pageCount > 3 && (
                  <button
                    className={safePage === pageCount ? 'is-active' : ''}
                    type="button"
                    onClick={() => setPage(pageCount)}
                  >
                    {pageCount}
                  </button>
                )}
                <button type="button" aria-label="Next page" disabled={safePage === pageCount} onClick={() => setPage((value) => Math.min(pageCount, value + 1))}><ChevronRight size={14} /></button>
              </div>
            </footer>
          </section>

          <ReservationDetailPanel selected={selectedReservation} activeTab={detailTab} onTabChange={setDetailTab} onStatus={updateStatus} onAction={setActionMessage} />
        </div>

        <AssistantPanel selected={selectedReservation} onAction={setActionMessage} />
      </section>
    </main>
  );
}
