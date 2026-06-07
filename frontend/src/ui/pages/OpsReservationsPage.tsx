import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  ArrowDownToLine,
  CalendarDays,
  ChevronRight,
  CheckCircle2,
  Filter,
  MessageSquareText,
  Search,
  ShieldCheck,
  Star,
  Users,
  XCircle,
} from 'lucide-react';
import { OpsReservationsFactory } from '../../application/OpsReservationsFactory';
import { OpsReservationRow, OpsReservationsSnapshot } from '../../domain/models';
import { OpsListModal } from '../components/OpsListModal';
import { formatStayName } from '../helpers/stayNames';

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

function sourceLabel(row: OpsReservationRow) {
  return row.recordType === 'airbnb' ? 'Airbnb import' : 'Direct request';
}

function contactLabel(row: OpsReservationRow) {
  if (row.email) return row.email;
  if (row.phone) return row.phone;
  if (row.threadUrl) return 'Airbnb thread available';
  return 'Needs contact';
}

export function OpsReservationsPage() {
  const service = useMemo(() => OpsReservationsFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsReservationsSnapshot | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const [isListOpen, setIsListOpen] = useState(false);
  const [visibleLimit, setVisibleLimit] = useState(2);

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

  const filteredRows = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    if (!query) return snapshot.rows;
    return snapshot.rows.filter((row) => (
      row.name.toLowerCase().includes(query)
      || row.listing.toLowerCase().includes(query)
      || row.feedback.toLowerCase().includes(query)
      || row.email.toLowerCase().includes(query)
      || row.segment.toLowerCase().includes(query)
    ));
  }, [search, snapshot]);

  const visibleRows = useMemo(() => {
    if (visibleLimit <= 0) return filteredRows;
    return filteredRows.slice(0, visibleLimit);
  }, [filteredRows, visibleLimit]);

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

  const renderReservationRow = (row: OpsReservationRow) => (
    <details className="ops-res-row ops-expand-card" data-segment={row.segmentValue || 'average'} key={`${row.recordType}-${row.id}`}>
      <summary className="ops-res-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <div className="ops-res-row__guest">
          <span className={`ops-res-source ops-res-source--${row.recordType}`}>{sourceLabel(row)}</span>
          <h3>{row.name}</h3>
          <p>{contactLabel(row)}</p>
        </div>
        <div className="ops-res-row__stay">
          <strong>{formatStayName(row.listing)}</strong>
          <span>{compactDate(row.stayDates)}</span>
          <small>{row.guests ? `${row.guests} guests` : 'Guest count pending'} {row.listingId ? `· ${row.listingId}` : ''}</small>
        </div>
        <div className="ops-res-row__feedback">
          <span className={`ops-status-pill ops-status-pill--${row.segmentValue || 'average'}`}>{row.segment || 'Average'}</span>
          <p>{row.consentStatus}</p>
        </div>
      </summary>
      <div className="ops-expand-details ops-res-details">
        <div>
          <span>Feedback</span>
          <p>{row.feedback || row.sourceSubject || 'No feedback captured yet.'}</p>
          {row.rating && <strong><Star size={14} /> {row.rating}</strong>}
        </div>
        <div>
          <span>Record links</span>
          <p>{row.updatedAt ? `Updated ${new Date(row.updatedAt).toLocaleString()}` : 'Update time pending'}</p>
        </div>
        <div className="ops-res-row__actions">
          {row.recordType === 'direct' && (
            <>
              <button type="button" onClick={() => updateStatus(row, 'reviewing')}><MessageSquareText size={14} /> Review</button>
              <button type="button" onClick={() => updateStatus(row, 'confirmed')}><CheckCircle2 size={14} /> Confirm</button>
              <button type="button" onClick={() => updateStatus(row, 'cancelled')}><XCircle size={14} /> Cancel</button>
            </>
          )}
          {row.threadUrl && <a href={row.threadUrl} target="_blank" rel="noreferrer">Airbnb thread</a>}
          <a href={row.recordAdminUrl}>Record</a>
          {row.profileAdminUrl && <a href={row.profileAdminUrl}>Profile</a>}
          {row.feedbackAdminUrl && <a href={row.feedbackAdminUrl}>Feedback</a>}
        </div>
      </div>
    </details>
  );

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return (
      <main className="dashboard-content ops-res-modern">
        <section className="ops-res-modern__hero">
          <span />
          <strong />
          <p />
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-content ops-res-modern">
      <section className="ops-res-modern__hero">
        <div>
          <span><CalendarDays size={16} /> Modern reservations CRM</span>
          <h2>Reservations CRM</h2>
          <p>Direct requests, Airbnb guests, feedback, and customer groups in one compact workflow.</p>
        </div>
        <div className="ops-res-modern__actions">
          <a href={snapshot.exportUrl}><ArrowDownToLine size={16} /> Export CSV</a>
          <a href="/admin/bookings/airbnbguestrecord/import/"><Users size={16} /> Import Airbnb guests</a>
          <a href="/admin/bookings/bookinginquiry/"><CalendarDays size={16} /> Booking admin</a>
        </div>
      </section>

      <section className="ops-res-metrics">
        {snapshot.summaryCards.slice(0, 7).map((card) => (
          <article key={`${card.label}-${card.value}`}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.caption}</p>
          </article>
        ))}
      </section>

      <section className="ops-res-controls">
        <label>
          <Search size={17} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search guests, stays, feedback, email, or group"
          />
        </label>
        <div className="ops-res-segment-row" aria-label="Customer group filters">
          <span><Filter size={15} /> Groups</span>
          {snapshot.segmentOptions.map((segment) => (
            <a
              className={segment.value === snapshot.selectedSegment ? 'is-active' : ''}
              data-segment={segment.value || 'all'}
              href={segment.url}
              key={segment.value || 'all'}
            >
              {segment.label}
              <small>{segment.count}</small>
            </a>
          ))}
        </div>
      </section>

      {actionMessage && <div className="ops-res-alert">{actionMessage}</div>}

      <section className="ops-res-list" aria-label="Reservations and imported Airbnb guests">
        <div className="ops-res-list__header">
          <div>
            <h3>{filteredRows.length} guests shown</h3>
            <p>{visibleRows.length} visible here. {snapshot.rows.length} total records available in the current segment.</p>
          </div>
          <div className="ops-card-heading__actions">
            <label className="ops-inline-select">
              Show
              <select value={visibleLimit} onChange={(event) => setVisibleLimit(Number(event.target.value))} aria-label="Reservations visible on page">
                <option value={2}>2</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={0}>All</option>
              </select>
            </label>
            <button type="button" onClick={() => setIsListOpen(true)}><Search size={15} /> Open list</button>
            <span><ShieldCheck size={15} /> Consent-aware CRM</span>
          </div>
        </div>

        {filteredRows.length === 0 && (
          <article className="ops-res-empty">
            <Users size={28} />
            <h3>No records match this filter yet.</h3>
            <p>Import Airbnb guests or clear the search to see the complete local customer list.</p>
          </article>
        )}

        <div className="ops-list-scroll">
          {visibleRows.map(renderReservationRow)}
        </div>
      </section>

      <OpsListModal
        isOpen={isListOpen}
        title={`${filteredRows.length} guests shown`}
        subtitle="Scroll the full reservation and imported Airbnb customer list."
        onClose={() => setIsListOpen(false)}
      >
        {filteredRows.map(renderReservationRow)}
      </OpsListModal>
    </main>
  );
}
