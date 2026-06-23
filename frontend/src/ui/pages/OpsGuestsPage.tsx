import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ChevronLeft, ChevronRight, Download, Filter, Search, UserPlus, UsersRound } from 'lucide-react';
import { GuestFactory } from '../../application/GuestFactory';
import { Guest, GuestDetailTab, GuestWorkspace } from '../../domain/guests';
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
  const [selectedGuestId, setSelectedGuestId] = useState('');
  const [activeTab, setActiveTab] = useState<GuestDetailTab>('messages');
  const [messageDraft, setMessageDraft] = useState('');
  const [messageConfirmed, setMessageConfirmed] = useState(false);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let mounted = true;
    service
      .loadWorkspace({ segment: new URLSearchParams(window.location.search).get('segment') || 'all' })
      .then((data) => {
        if (!mounted) return;
        setWorkspace(data);
        setSegment(data.filters.segment || 'all');
        setSelectedGuestId(new URLSearchParams(window.location.search).get('guest') || data.guests[0]?.id || '');
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load guests.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const visibleGuests = useMemo(() => {
    if (!workspace) return [];
    return service.filterGuests(workspace, { query: search, segment });
  }, [search, segment, service, workspace]);

  const selectedGuest = useMemo(() => {
    if (!workspace) return null;
    const scopedGuest = visibleGuests.find((guest) => guest.id === selectedGuestId);
    return scopedGuest ?? service.selectGuest(workspace, selectedGuestId) ?? visibleGuests[0] ?? null;
  }, [selectedGuestId, service, visibleGuests, workspace]);

  useEffect(() => {
    if (selectedGuest && selectedGuest.id !== selectedGuestId) {
      setSelectedGuestId(selectedGuest.id);
    }
  }, [selectedGuest, selectedGuestId]);

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
    const rows = visibleGuests.map((guest) => {
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
          <button className={segment === tab.value ? 'is-active' : ''} key={tab.value} onClick={() => setSegment(tab.value)} type="button">
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
              <input onChange={(event) => setSearch(event.target.value)} placeholder="Search guests by name, email, phone, or reservation..." value={search} />
            </label>
            <button type="button">
              <Filter size={15} />
              Filters
            </button>
          </div>
          <GuestTable
            guests={visibleGuests}
            onSelect={(guest) => {
              setSelectedGuestId(guest.id);
              setActiveTab('messages');
            }}
            selectedGuestId={selectedGuest?.id || ''}
          />
          <div className="guests-pagination">
            <span>Showing 1 to {Math.min(visibleGuests.length, 10)} of {visibleGuests.length} guests</span>
            <div>
              <button aria-label="Previous page" type="button"><ChevronLeft size={15} /></button>
              <button className="is-active" type="button">1</button>
              <button type="button">2</button>
              <button type="button">3</button>
              <button aria-label="Next page" type="button"><ChevronRight size={15} /></button>
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
