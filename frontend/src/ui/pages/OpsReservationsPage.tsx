import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  ChevronRight,
  Clock3,
  Download,
  FileText,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Users,
} from 'lucide-react';
import { OpsReservationsFactory } from '../../application/OpsReservationsFactory';
import { OpsReservationsSnapshot } from '../../domain/models';
import {
  OpsReservation,
  type ReservationDetailTab,
  type ReservationStatusFilter,
} from '../../domain/reservations';

function formatTimestamp(value: string) {
  if (!value) return 'Ready';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Updated recently';
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function StatusBadge({ reservation }: { reservation: OpsReservation }) {
  return (
    <span className={`ops-res-v4-badge ops-res-v4-badge--${reservation.statusFilter}`}>
      {reservation.status.label}
    </span>
  );
}

function MoneyBadge({
  tone,
  label,
  amount,
}: {
  tone: 'paid' | 'hold' | 'pending' | 'none' | 'unpaid';
  label: string;
  amount: string;
}) {
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
  active: ReservationStatusFilter;
  counts: Record<ReservationStatusFilter, number>;
  onChange: (status: ReservationStatusFilter) => void;
}) {
  const tabs: Array<{ id: ReservationStatusFilter; label: string; dot?: string }> = [
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

function DetailTabContent({
  selected,
  activeTab,
}: {
  selected: OpsReservation;
  activeTab: ReservationDetailTab;
}) {
  if (activeTab === 'payments') {
    return (
      <>
        {selected.paymentPlan.steps.map((step) => (
          <div className="ops-res-v4-message-card" key={step.label}>
            <FileText size={18} />
            <p>
              <strong>{step.label}</strong>
              {step.amount.withCurrencySuffix()} - {step.dueLabel}
            </p>
            <time>{step.status}</time>
          </div>
        ))}
      </>
    );
  }

  if (activeTab === 'deposits') {
    return (
      <div className="ops-res-v4-message-card">
        <ShieldCheck size={18} />
        <p>
          <strong>{selected.depositHold.label}</strong>
          {selected.depositHold.amount.withCurrencySuffix()} through {selected.depositHold.provider || 'MLADIS checkout'}
        </p>
        <time>{selected.depositHold.status}</time>
      </div>
    );
  }

  if (activeTab === 'documents') {
    return (
      <>
        <div className="ops-res-v4-message-card">
          <FileText size={18} />
          <p>
            <strong>Property Rules</strong>
            Version {selected.documents.propertyRulesVersion}
          </p>
          <time>{selected.documents.propertyRulesAccepted ? 'Accepted' : 'Pending'}</time>
        </div>
        <div className="ops-res-v4-message-card">
          <FileText size={18} />
          <p>
            <strong>Damage Deposit Hold Terms</strong>
            Version {selected.documents.damageTermsVersion}
          </p>
          <time>{selected.documents.damageTermsAccepted ? 'Accepted' : 'Pending'}</time>
        </div>
      </>
    );
  }

  if (activeTab === 'activity') {
    return (
      <>
        {selected.timeline.map((event) => (
          <div className="ops-res-v4-message-card" key={`${event.type}-${event.timestamp}-${event.label}`}>
            <Clock3 size={18} />
            <p>
              <strong>{event.label}</strong>
              {event.note}
            </p>
            <time>{formatTimestamp(event.timestamp)}</time>
          </div>
        ))}
      </>
    );
  }

  return (
    <>
      {selected.messages.items.map((message) => (
        <div className={`ops-res-v4-message-card${message.fromStaff ? ' is-reply' : ''}`} key={message.id}>
          <div className={`ops-res-v4-avatar is-small${message.fromStaff ? ' is-owner' : ''}`}>
            {message.fromStaff ? 'PG' : selected.initials}
          </div>
          <p>
            <strong>{message.senderLabel}</strong>
            {message.body}
          </p>
          <time>{formatTimestamp(message.timestamp)}</time>
        </div>
      ))}
    </>
  );
}

function ReservationDetailPanel({
  selected,
  activeTab,
  onTabChange,
}: {
  selected: OpsReservation | undefined;
  activeTab: ReservationDetailTab;
  onTabChange: (tab: ReservationDetailTab) => void;
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

  const tabs: ReservationDetailTab[] = ['messages', 'payments', 'deposits', 'documents', 'activity'];
  const depositUrl = `/ops/deposits/?search=${encodeURIComponent(selected.requestKey)}`;
  const paymentsUrl = `/ops/payments/?search=${encodeURIComponent(selected.requestKey)}`;

  return (
    <section className="ops-res-v4-detail">
      <aside className="ops-res-v4-guest-card">
        <div className="ops-res-v4-avatar">{selected.initials}</div>
        <div>
          <h3>{selected.guest.name}</h3>
          <StatusBadge reservation={selected} />
          <p>{selected.guest.contactLabel}</p>
          <small>{selected.guest.country}</small>
        </div>
        <div className="ops-res-v4-mini-actions">
          {selected.guest.profileAdminUrl && <a href={selected.guest.profileAdminUrl}>View profile</a>}
          {selected.guest.threadUrl && <a href={selected.guest.threadUrl} target="_blank" rel="noreferrer">Message guest</a>}
        </div>
        <section>
          <header>
            <strong>Booking Summary</strong>
            <a href={selected.admin.record_url}>Edit</a>
          </header>
          <dl>
            <dt>Listing</dt>
            <dd>{selected.stay.name}</dd>
            <dt>Check-in / Out</dt>
            <dd>{selected.dates.displayRange}</dd>
            <dt>Nights</dt>
            <dd>{selected.dates.nightsLabel}</dd>
            <dt>Guests</dt>
            <dd>{selected.guestsLabel} guests</dd>
            <dt>Total Amount</dt>
            <dd>{selected.paymentPlan.total.withCurrencySuffix()}</dd>
          </dl>
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

        <DetailTabContent selected={selected} activeTab={activeTab} />
      </div>

      <aside className="ops-res-v4-deposit-panel">
        <header>
          <h3>Deposit Hold</h3>
          <span>{selected.depositHold.label}</span>
        </header>
        <strong>{selected.depositHold.amount.withCurrencySuffix()}</strong>
        <p>Requested for {selected.guest.name}</p>
        <small><Clock3 size={14} /> {selected.depositHold.expiresAt || 'Managed by reservation timeline'}</small>
        <div className="ops-res-v4-related-links">
          <a href={depositUrl}>Open deposit hold</a>
          <a href={paymentsUrl}>Open payments</a>
        </div>
        <section>
          <h4>Payment Timeline</h4>
          <ol>
            {selected.paymentPlan.steps.map((step) => (
              <li key={step.label}>
                <i />
                <span>{step.label}</span>
                <em>{step.amount.display}</em>
              </li>
            ))}
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
  const [selectedStatus, setSelectedStatus] = useState<ReservationStatusFilter>('all');
  const [selectedKey, setSelectedKey] = useState('');
  const [listingFilter, setListingFilter] = useState('All listings');
  const [channelFilter, setChannelFilter] = useState('All channels');
  const [countryFilter, setCountryFilter] = useState('All countries');
  const [riskFilter, setRiskFilter] = useState('All levels');
  const [detailTab, setDetailTab] = useState<ReservationDetailTab>('messages');
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

  const reservations = snapshot?.reservations ?? [];
  const statusCounts = useMemo(() => service.statusCounts(reservations), [reservations, service]);
  const options = useMemo(() => service.reservationOptions(reservations), [reservations, service]);
  const filteredRows = useMemo(() => service.filterReservations(reservations, {
    search,
    status: selectedStatus,
    listing: listingFilter,
    channel: channelFilter,
    country: countryFilter,
    risk: riskFilter,
  }), [channelFilter, countryFilter, listingFilter, reservations, riskFilter, search, selectedStatus, service]);

  const pageSize = 5;
  const pageCount = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const safePage = Math.min(page, pageCount);
  const visibleRows = filteredRows.slice((safePage - 1) * pageSize, safePage * pageSize);
  const selectedReservation = filteredRows.find((reservation) => (
    reservation.key === selectedKey
    || reservation.id === selectedKey
    || reservation.requestKey === selectedKey
  ));
  const pageStart = filteredRows.length === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const pageEnd = Math.min(safePage * pageSize, filteredRows.length);
  const visiblePageButtons = Array.from({ length: Math.min(3, pageCount) }, (_, index) => index + 1);

  useEffect(() => {
    setPage(1);
  }, [channelFilter, countryFilter, listingFilter, riskFilter, search, selectedStatus]);

  useEffect(() => {
    if (page > pageCount) setPage(pageCount);
  }, [page, pageCount]);

  useEffect(() => {
    if (!snapshot || !selectedKey) return;
    if (!selectedReservation) {
      setSelectedKey('');
      setDetailTab('messages');
    }
  }, [selectedKey, selectedReservation, snapshot]);

  function resetFilters() {
    setSearch('');
    setListingFilter('All listings');
    setChannelFilter('All channels');
    setCountryFilter('All countries');
    setRiskFilter('All levels');
    setSelectedStatus('all');
  }

  function toggleSelection(reservation: OpsReservation) {
    setSelectedKey((current) => current === reservation.key ? '' : reservation.key);
    setDetailTab('messages');
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
          <p>Review real guest, stay, payment, deposit, document, and timeline records.</p>
        </div>
        <div className="ops-res-v4-title-actions">
          <button type="button" onClick={() => setShowAdvancedFilters((value) => !value)}>
            <SlidersHorizontal size={15} /> Filters
          </button>
          <a href={snapshot.exportUrl}><Download size={15} /> Export</a>
        </div>
      </section>

      <ReservationTabs active={selectedStatus} counts={statusCounts} onChange={setSelectedStatus} />

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
                <kbd>Cmd F</kbd>
              </label>
              <WorkspaceSelect label="Listing" value={listingFilter} options={options.listings} onChange={setListingFilter} />
              <WorkspaceSelect label="Channel" value={channelFilter} options={options.channels} onChange={setChannelFilter} />
              <WorkspaceSelect label="Source Country" value={countryFilter} options={options.countries} onChange={setCountryFilter} />
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
                      onClick={() => toggleSelection(reservation)}
                    >
                      <td>
                        <input
                          checked={selectedReservation?.key === reservation.key}
                          onClick={(event) => event.stopPropagation()}
                          onChange={() => toggleSelection(reservation)}
                          type="checkbox"
                        />
                      </td>
                      <td>
                        <div className="ops-res-v4-guest">
                          <span className="ops-res-v4-avatar">{reservation.initials}</span>
                          <span>
                            <strong>{reservation.guest.name}</strong>
                            <small>{reservation.guest.contactLabel}</small>
                          </span>
                        </div>
                      </td>
                      <td>
                        <strong>{reservation.stay.name}</strong>
                        <small>#{reservation.stay.displayId}</small>
                      </td>
                      <td>
                        <span>{reservation.dates.displayRange}</span>
                        <small>{reservation.dates.nightsLabel}</small>
                      </td>
                      <td><strong>{reservation.guestsLabel}</strong> <Users size={13} /></td>
                      <td>
                        <MoneyBadge
                          tone={reservation.depositHold.tone}
                          label={reservation.depositHold.label}
                          amount={reservation.depositHold.amount.display}
                        />
                      </td>
                      <td>
                        <MoneyBadge
                          tone={reservation.paymentPlan.tone}
                          label={reservation.paymentPlan.label}
                          amount={reservation.paymentPlan.total.display}
                        />
                      </td>
                      <td>
                        <span>{reservation.channel}</span>
                        <small>{reservation.guest.country}</small>
                      </td>
                      <td><span className={`ops-res-v4-risk ops-res-v4-risk--${reservation.risk.level}`}>{reservation.risk.label}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <footer className="ops-res-v4-table-footer">
              <span>Showing {pageStart} to {pageEnd} of {filteredRows.length} results</span>
              <div>
                <button
                  type="button"
                  aria-label="Previous page"
                  disabled={safePage === 1}
                  onClick={() => {
                    setSelectedKey('');
                    setPage((value) => Math.max(1, value - 1));
                  }}
                >
                  <ChevronRight size={14} />
                </button>
                {visiblePageButtons.map((pageNumber) => (
                  <button
                    className={safePage === pageNumber ? 'is-active' : ''}
                    key={pageNumber}
                    type="button"
                    onClick={() => {
                      setSelectedKey('');
                      setPage(pageNumber);
                    }}
                  >
                    {pageNumber}
                  </button>
                ))}
                {pageCount > 4 && <span>...</span>}
                {pageCount > 3 && (
                  <button
                    className={safePage === pageCount ? 'is-active' : ''}
                    type="button"
                    onClick={() => {
                      setSelectedKey('');
                      setPage(pageCount);
                    }}
                  >
                    {pageCount}
                  </button>
                )}
                <button
                  type="button"
                  aria-label="Next page"
                  disabled={safePage === pageCount}
                  onClick={() => {
                    setSelectedKey('');
                    setPage((value) => Math.min(pageCount, value + 1));
                  }}
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </footer>
          </section>

          <ReservationDetailPanel
            selected={selectedReservation}
            activeTab={detailTab}
            onTabChange={setDetailTab}
          />
        </div>
      </section>
    </main>
  );
}
