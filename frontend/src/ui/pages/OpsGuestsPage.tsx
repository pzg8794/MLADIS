import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ChevronLeft, ChevronRight, Download, Filter, Search, UserPlus, UsersRound } from 'lucide-react';
import { GuestFactory } from '../../application/GuestFactory';
import { Guest, GuestDetailTab, GuestWorkspace, GuestWorkspaceFilters } from '../../domain/guests';
import {
  GuestDetailPanel,
  GuestLinkedStaysPanel,
  GuestMessageComposer,
  GuestProfileCard,
} from '../components/guests/GuestPanels';
import './ops-guests-page.css';

export function OpsGuestsPage({ compatibilityRoute = 'guests' }: { compatibilityRoute?: 'guests' | 'customers' }) {
  const service = useMemo(() => GuestFactory.create(), []);
  const [workspace, setWorkspace] = useState<GuestWorkspace | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('all');
  const [source, setSource] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [selectedGuestId, setSelectedGuestId] = useState('');
  const [activeTab, setActiveTab] = useState<GuestDetailTab>('messages');
  const [messageDraft, setMessageDraft] = useState('');
  const [messageConfirmed, setMessageConfirmed] = useState(false);
  const [notice, setNotice] = useState('');
  const pageSize = 10;

  useEffect(() => {
    let mounted = true;
    service
      .loadWorkspace()
      .then((data) => {
        if (!mounted) return;
        const query = new URLSearchParams(window.location.search);
        const initialSearch = query.get('search') || data.filters.search || '';
        const initialSegment = query.get('segment') || data.filters.segment || 'all';
        const initialSource = query.get('source') || data.filters.source || '';
        const initialStatus = query.get('status') || data.filters.status || '';
        const initialFilters = {
          query: initialSearch,
          segment: initialSegment,
          source: initialSource,
          status: initialStatus,
        };
        const requestedGuestId = query.get('guest') || '';
        const requestedGuest = requestedGuestId
          ? data.guests.find((guest) => guest.id === requestedGuestId || guest.key === requestedGuestId)
          : null;
        const requestedGuestIsVisible = requestedGuest
          ? service.filterGuests(data, initialFilters).some((guest) => guest.id === requestedGuest.id)
          : false;
        setWorkspace(data);
        setSearch(initialSearch);
        setSegment(initialSegment);
        setSource(initialSource);
        setStatus(initialStatus);
        setSelectedGuestId(requestedGuestIsVisible && requestedGuest ? requestedGuest.id : '');
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load guests.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const filters = useMemo<GuestWorkspaceFilters>(() => ({
    query: search,
    segment,
    source,
    status,
  }), [search, segment, source, status]);

  const visibleGuests = useMemo(() => {
    if (!workspace) return [];
    return workspace.paginationProjection(page, pageSize, filters).guests;
  }, [filters, page, workspace]);

  const filteredGuests = useMemo(() => {
    if (!workspace) return [];
    return service.filterGuests(workspace, filters);
  }, [filters, service, workspace]);

  const pagination = useMemo(() => {
    if (!workspace) return null;
    return workspace.paginationProjection(page, pageSize, filters);
  }, [filters, page, workspace]);

  const filterOptions = useMemo(() => workspace?.filterOptions(), [workspace]);

  const selectedGuest = useMemo(() => {
    if (!selectedGuestId) return null;
    return filteredGuests.find((guest) => guest.id === selectedGuestId || guest.key === selectedGuestId) ?? null;
  }, [filteredGuests, selectedGuestId]);

  const pageNumbers = useMemo(() => {
    if (!pagination) return [];
    const candidates = new Set([1, pagination.pageCount, pagination.page - 1, pagination.page, pagination.page + 1]);
    return Array.from(candidates)
      .filter((pageNumber) => pageNumber >= 1 && pageNumber <= pagination.pageCount)
      .sort((left, right) => left - right);
  }, [pagination]);

  async function sendMessage() {
    if (!selectedGuest || !messageDraft.trim()) return;
    setNotice('');
    try {
      const result = await service.sendMessage(selectedGuest, messageDraft, messageConfirmed);
      setNotice(result.message.status === 'sent' ? 'Confirmed message sent through the approved channel.' : 'Draft staged. Check staff approval before sending.');
      setMessageDraft('');
      setMessageConfirmed(false);
    } catch (caught) {
      setNotice(caught instanceof Error ? caught.message : 'Could not process this guest message.');
    }
  }

  function exportVisibleGuests() {
    const header = ['Name', 'Email', 'Phone', 'Country', 'Source', 'Past stays', 'Total spend', 'Segment', 'Last contact'];
    const rows = filteredGuests.map((guest) => {
      const row = guest.rowProjection();
      return [
        row.name,
        row.email,
        row.phone,
        row.country,
        row.source,
        String(row.past_stays),
        row.total_spend.with_currency,
        row.segment.label,
        row.last_contact_label,
      ];
    });
    const csv = [header, ...rows]
      .map((values) => values.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'mladis-guests.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  function clearFilters() {
    const nextFilters = { query: '', segment: 'all', source: '', status: '' };
    setSearch(nextFilters.query);
    setSegment(nextFilters.segment);
    setSource(nextFilters.source);
    setStatus(nextFilters.status);
    setPage(1);
    clearSelectionIfFilteredOut(nextFilters);
  }

  function clearGuestSelection() {
    setSelectedGuestId('');
    setActiveTab('messages');
    setMessageDraft('');
    setMessageConfirmed(false);
    setNotice('');
  }

  function toggleGuestSelection(guest: Guest) {
    if (selectedGuestId === guest.id) {
      clearGuestSelection();
      return;
    }

    setSelectedGuestId(guest.id);
    setActiveTab('messages');
    setMessageDraft('');
    setMessageConfirmed(false);
    setNotice('');
  }

  function clearSelectionIfFilteredOut(nextFilters: GuestWorkspaceFilters) {
    if (!workspace || !selectedGuestId) return;
    const stillVisible = service
      .filterGuests(workspace, nextFilters)
      .some((guest) => guest.id === selectedGuestId || guest.key === selectedGuestId);
    if (!stillVisible) clearGuestSelection();
  }

  function updateSearch(nextSearch: string) {
    const nextFilters = { query: nextSearch, segment, source, status };
    setSearch(nextSearch);
    setPage(1);
    clearSelectionIfFilteredOut(nextFilters);
  }

  function updateSegment(nextSegment: string) {
    const nextFilters = { query: search, segment: nextSegment, source, status };
    setSegment(nextSegment);
    setPage(1);
    clearSelectionIfFilteredOut(nextFilters);
  }

  function updateSource(nextSource: string) {
    const nextFilters = { query: search, segment, source: nextSource, status };
    setSource(nextSource);
    setPage(1);
    clearSelectionIfFilteredOut(nextFilters);
  }

  function updateStatus(nextStatus: string) {
    const nextFilters = { query: search, segment, source, status: nextStatus };
    setStatus(nextStatus);
    setPage(1);
    clearSelectionIfFilteredOut(nextFilters);
  }

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!workspace) {
    return <main className="dashboard-content guests-page"><section className="guests-loading-card" /></main>;
  }

  return (
    <main className="dashboard-content guests-page" data-compatibility-route={compatibilityRoute}>
      <section className="guests-header">
        <div>
          <h1>Guests</h1>
          <p>Manage guest relationships, profiles, travel details, and communication history.</p>
        </div>
        <div className="guests-header-actions">
          <a href="/admin/bookings/customerprofile/add/">
            <UserPlus size={16} />
            New guest
          </a>
          <button onClick={exportVisibleGuests} type="button">
            <Download size={16} />
            Export
          </button>
        </div>
      </section>

      <section className="guests-metric-grid">
        {workspace.metricsProjection().map((metric) => (
          <article className={`guests-metric-card guests-metric-card--${metric.tone}`} key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <p>{metric.caption}</p>
          </article>
        ))}
      </section>

      <section className="guests-tabs" aria-label="Guest segments">
        {workspace.segmentTabs().map((tab) => (
          <button className={segment === tab.value ? 'is-active' : ''} key={tab.value} onClick={() => updateSegment(tab.value)} type="button">
            {tab.label}
            <span>{tab.count}</span>
          </button>
        ))}
      </section>

      <section className="guests-workspace-grid">
        <div className="guests-list-card">
          <div className="guests-filter-row">
            <label>
              <Search size={16} />
              <input onChange={(event) => updateSearch(event.target.value)} placeholder="Search guests by name, email, phone, or reservation..." value={search} />
            </label>
            <label className="guests-filter-select">
              <Filter size={15} />
              <select aria-label="Filter guests by source" onChange={(event) => updateSource(event.target.value)} value={source}>
                <option value="">All channels</option>
                {filterOptions?.sources.map((option) => (
                  <option key={option.value} value={option.value}>{option.label} ({option.count})</option>
                ))}
              </select>
            </label>
            <label className="guests-filter-select">
              <select aria-label="Filter guests by status" onChange={(event) => updateStatus(event.target.value)} value={status}>
                <option value="">All statuses</option>
                {filterOptions?.statuses.map((option) => (
                  <option key={option.value} value={option.value}>{option.label} ({option.count})</option>
                ))}
              </select>
            </label>
            {(search || segment !== 'all' || source || status) && (
              <button onClick={clearFilters} type="button">Clear</button>
            )}
          </div>
          <GuestTable
            guests={visibleGuests}
            onSelect={toggleGuestSelection}
            selectedGuestId={selectedGuest?.id || ''}
          />
          <div className="guests-pagination">
            <span>
              Showing {pagination?.start ?? 0} to {pagination?.end ?? 0} of {pagination?.total ?? 0} guests
            </span>
            <div>
              <button aria-label="Previous page" disabled={!pagination || pagination.page <= 1} onClick={() => setPage((value) => Math.max(value - 1, 1))} type="button">
                <ChevronLeft size={15} />
              </button>
              {pageNumbers.map((pageNumber) => (
                <button className={pagination?.page === pageNumber ? 'is-active' : ''} key={pageNumber} onClick={() => setPage(pageNumber)} type="button">
                  {pageNumber}
                </button>
              ))}
              <button aria-label="Next page" disabled={!pagination || pagination.page >= pagination.pageCount} onClick={() => setPage((value) => value + 1)} type="button">
                <ChevronRight size={15} />
              </button>
            </div>
          </div>
        </div>

        <aside className="guests-side-column">
          {selectedGuest ? (
            <>
              <GuestProfileCard guest={selectedGuest} />
              <GuestMessageComposer
                confirmed={messageConfirmed}
                disabled={!selectedGuest.canMessage}
                draft={messageDraft}
                notice={notice}
                onConfirmedChange={setMessageConfirmed}
                onDraftChange={setMessageDraft}
                onSend={sendMessage}
              />
            </>
          ) : (
            <article className="guests-empty-selection">
              <UsersRound size={24} />
              <h3>Select a guest</h3>
              <p>Choose a guest to inspect profile, reservations, payments, deposits, and activity.</p>
            </article>
          )}
        </aside>
      </section>

      {selectedGuest && (
        <section className="guests-bottom-grid">
          <GuestDetailPanel activeTab={activeTab} guest={selectedGuest} onTabChange={setActiveTab} />
          <GuestLinkedStaysPanel guest={selectedGuest} />
        </section>
      )}
    </main>
  );
}

function GuestTable({
  guests,
  onSelect,
  selectedGuestId,
}: {
  guests: Guest[];
  onSelect: (guest: Guest) => void;
  selectedGuestId: string;
}) {
  if (!guests.length) {
    return (
      <div className="guests-empty-table">
        <UsersRound size={24} />
        <h3>No guests match this view.</h3>
        <p>Adjust search or segment filters.</p>
      </div>
    );
  }

  return (
    <div className="guests-table" role="table" aria-label="Guests">
      <div className="guests-table__head" role="row">
        <span role="columnheader">Guest</span>
        <span role="columnheader">Country</span>
        <span role="columnheader">Channel</span>
        <span role="columnheader">Past Stays</span>
        <span role="columnheader">Total Spend</span>
        <span role="columnheader">Status</span>
        <span role="columnheader">Last Contact</span>
      </div>
      {guests.map((guest) => {
        const row = guest.rowProjection();
        return (
          <button
            className={guest.id === selectedGuestId ? 'guests-table__row is-selected' : 'guests-table__row'}
            key={guest.id}
            onClick={() => onSelect(guest)}
            role="row"
            type="button"
          >
            <span className="guests-table__person" role="cell">
              <span className="guests-avatar">{row.initials}</span>
              <span>
                <strong>{row.name}</strong>
                <small>{row.email || row.phone || 'Needs contact details'}</small>
              </span>
            </span>
            <span role="cell">{row.country}</span>
            <span role="cell">{row.source}</span>
            <span role="cell">{row.past_stays}</span>
            <span role="cell">{row.total_spend.display}</span>
            <span role="cell"><mark className={`guests-status guests-status--${row.segment.tone}`}>{row.segment.label}</mark></span>
            <span role="cell">{row.last_contact_label || 'No contact yet'}</span>
          </button>
        );
      })}
    </div>
  );
}
