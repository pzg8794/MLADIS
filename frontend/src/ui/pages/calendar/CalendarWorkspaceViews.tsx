import { CSSProperties, ReactNode, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  DollarSign,
  Home,
  MapPin,
  Search,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react';
import { OpsCalendarDay, OpsCalendarEvent, OpsCalendarStayRow, OpsCalendarViewMode } from '../../../domain/models';

type StayVisualMeta = {
  index: number;
  color: string;
  bgColor: string;
  textColor: string;
  shortLabel: string;
  displayName: string;
  unitLabel: string;
  capacityLabel: string;
};

type StayRowWithMeta = {
  row: OpsCalendarStayRow;
  meta: StayVisualMeta;
};

type CalendarEventKind = 'all' | 'reservation' | 'block' | 'price';
type TimeFilter = 'all' | 'today' | 'upcoming' | 'past';

const timeSlots = [
  '09:00 - 10:00',
  '10:00 - 11:00',
  '11:00 - 12:00',
  '12:00 - 13:00',
  '13:00 - 14:00',
  '14:00 - 15:00',
  '15:00 - 16:00',
  '16:00 - 17:00',
  '17:00 - 18:00',
];

function isoToday() {
  return new Date().toISOString().slice(0, 10);
}

function dateFromIso(value: string) {
  return new Date(`${value}T00:00:00`);
}

function compactDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dateFromIso(value));
}

function fullDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(dateFromIso(value));
}

function monthKey(value: string) {
  return value.slice(0, 7);
}

function monthLabel(value: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(dateFromIso(`${monthKey(value)}-01`));
}

function shortPeriodDate(value: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dateFromIso(value));
}

function eventCoversDay(event: OpsCalendarEvent, date: string) {
  if (event.type === 'reservation') {
    return event.start <= date && date < event.end;
  }
  return event.start <= date && date <= event.end;
}

function eventTone(event: OpsCalendarEvent) {
  if (event.type === 'reservation') return 'reservation';
  if (event.type === 'block') return 'block';
  return 'price';
}

function uniqueEvents(rows: StayRowWithMeta[]) {
  const seen = new Map<string, OpsCalendarEvent>();
  rows.forEach(({ row }) => row.events.forEach((event) => seen.set(event.id, event)));
  return Array.from(seen.values()).sort((a, b) => a.start.localeCompare(b.start) || a.title.localeCompare(b.title));
}

function eventMatchesQuery(event: OpsCalendarEvent, query: string, meta?: StayVisualMeta) {
  if (!query) return true;
  return [
    event.title,
    event.subtitle,
    event.itemName,
    event.guestLabel,
    event.rangeLabel,
    event.status,
    meta?.shortLabel || '',
    meta?.displayName || '',
    meta?.unitLabel || '',
  ].some((value) => value.toLowerCase().includes(query));
}

function isFutureOrToday(value: string) {
  return value >= isoToday();
}

function isPast(value: string) {
  return value < isoToday();
}

function firstMonthDays(rows: StayRowWithMeta[]) {
  const days = rows[0]?.row.weeks.flat() || [];
  const seen = new Map<string, OpsCalendarDay>();
  days.filter((day) => day.inMonth).forEach((day) => seen.set(day.date, day));
  return Array.from(seen.values());
}

function fallbackVisibleDays(rows: StayRowWithMeta[], view: OpsCalendarViewMode, focusDate: string, visibleDays: OpsCalendarDay[]) {
  const firstRow = rows[0]?.row;
  if (!firstRow) return [];
  if (view === 'month') return firstMonthDays(rows);
  if (visibleDays.length > 0) return visibleDays;
  if (view === 'week') return firstRow.weekDays;
  return firstRow.weeks.flat().filter((day) => day.date === focusDate);
}

function periodLabel(view: OpsCalendarViewMode, focusDate: string, days: OpsCalendarDay[]) {
  if (view === 'month') return monthLabel(focusDate);
  if (days.length === 0) return fullDate(focusDate);
  if (view === 'list') return fullDate(days[0].date);
  return `${shortPeriodDate(days[0].date)} - ${shortPeriodDate(days[days.length - 1].date)}, ${dateFromIso(days[days.length - 1].date).getFullYear()}`;
}

function cleanCalendarSubtitle(value?: string) {
  return (value || 'Direct booking calendar')
    .replace(/^MLADIS\s*[-–—]\s*/i, '')
    .replace(/\bBedrooms?\b/gi, 'Beds')
    .replace(/\s+/g, ' ')
    .trim();
}

function periodTitle(view: OpsCalendarViewMode) {
  if (view === 'month') return 'This Month';
  if (view === 'week') return 'This Week';
  return 'Selected Day';
}

function eventOverlapsDates(event: OpsCalendarEvent, dates: string[]) {
  return dates.some((date) => eventCoversDay(event, date));
}

function listEntryDate(event: OpsCalendarEvent, dates: string[]) {
  if (dates.includes(event.start)) return event.start;
  return dates.find((date) => eventCoversDay(event, date)) || event.start;
}

function stayMeta(rows: StayRowWithMeta[], itemId: number) {
  return rows.find(({ row }) => row.stay.id === itemId)?.meta;
}

function stayEvents(rows: StayRowWithMeta[], itemId: number) {
  return rows.find(({ row }) => row.stay.id === itemId)?.row.events || [];
}

export function CalendarListView({
  rows,
  view,
  focusDate,
  globalSearch,
  visibleDays,
}: {
  rows: StayRowWithMeta[];
  view: OpsCalendarViewMode;
  focusDate: string;
  globalSearch: string;
  visibleDays: OpsCalendarDay[];
}) {
  const [search, setSearch] = useState('');
  const [stayFilter, setStayFilter] = useState<number | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<CalendarEventKind>('all');
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');
  const [expandedDate, setExpandedDate] = useState<string | null>(null);
  const periodDays = useMemo(() => fallbackVisibleDays(rows, view, focusDate, visibleDays), [focusDate, rows, view, visibleDays]);
  const periodDates = useMemo(() => periodDays.map((day) => day.date), [periodDays]);

  useEffect(() => {
    setExpandedDate(null);
  }, [focusDate, view]);

  const filteredEvents = useMemo(() => {
    const query = search.trim().toLowerCase();
    const globalQuery = globalSearch.trim().toLowerCase();
    return uniqueEvents(rows).filter((event) => {
      const meta = stayMeta(rows, event.itemId);
      const matchesStay = stayFilter === 'all' || event.itemId === stayFilter;
      const matchesType = typeFilter === 'all' || event.type === typeFilter;
      const matchesPeriod = eventOverlapsDates(event, periodDates);
      const matchesTime = timeFilter === 'all'
        || (timeFilter === 'today' && event.start <= isoToday() && event.end >= isoToday())
        || (timeFilter === 'upcoming' && isFutureOrToday(event.start))
        || (timeFilter === 'past' && isPast(event.end));
      return matchesStay && matchesType && matchesPeriod && matchesTime && eventMatchesQuery(event, query, meta) && eventMatchesQuery(event, globalQuery, meta);
    });
  }, [globalSearch, periodDates, rows, search, stayFilter, timeFilter, typeFilter]);

  const grouped = useMemo(() => {
    const map = new Map<string, OpsCalendarEvent[]>();
    filteredEvents.forEach((event) => {
      const date = listEntryDate(event, periodDates);
      if (!map.has(date)) map.set(date, []);
      map.get(date)?.push(event);
    });
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [filteredEvents, periodDates]);

  return (
    <section className="calendar-subview calendar-list-view">
      <div className="calendar-list-filterbar">
        <label>
          <Search size={17} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search bookings, stays, guests..." />
        </label>
        <div className="calendar-select-wrap">
          <Building2 size={17} />
          <select value={stayFilter} onChange={(event) => setStayFilter(event.target.value === 'all' ? 'all' : Number(event.target.value))}>
            <option value="all">All</option>
            {rows.map(({ row, meta }) => <option key={row.stay.id} value={row.stay.id}>{meta.displayName}</option>)}
          </select>
          <ChevronDown size={15} />
        </div>
        <div className="calendar-filter-toggles">
          {(['all', 'reservation', 'block', 'price'] as CalendarEventKind[]).map((kind) => (
            <button className={typeFilter === kind ? 'is-active' : ''} key={kind} type="button" onClick={() => setTypeFilter(kind)}>
              {kind === 'all' ? 'All' : kind}
            </button>
          ))}
        </div>
        <div className="calendar-filter-toggles">
          {(['all', 'today', 'upcoming', 'past'] as TimeFilter[]).map((kind) => (
            <button className={timeFilter === kind ? 'is-active' : ''} key={kind} type="button" onClick={() => setTimeFilter(kind)}>
              {kind}
            </button>
          ))}
        </div>
        <strong>{filteredEvents.length} records · {periodLabel(view, focusDate, periodDays)}</strong>
      </div>

      <div className="calendar-list-body">
        {grouped.length === 0 ? (
          <EmptyCalendarState title="No bookings found" body="Change the search or filters to widen the list." />
        ) : grouped.map(([date, events]) => {
          const isOpen = expandedDate === date;
          const roomDots = Array.from(new Set(events.map((event) => event.itemId)))
            .map((itemId) => stayMeta(rows, itemId))
            .filter(Boolean) as StayVisualMeta[];
          return (
            <article className="calendar-list-date-group" key={date}>
              <button type="button" onClick={() => setExpandedDate(isOpen ? '' : date)}>
                <span className={date === isoToday() ? 'is-today' : ''}>
                  <b>{new Intl.DateTimeFormat('en-US', { weekday: 'short' }).format(dateFromIso(date))}</b>
                  <strong>{dateFromIso(date).getDate()}</strong>
                </span>
                <div>
                  <strong>{date === isoToday() ? 'Today · ' : ''}{fullDate(date)}</strong>
                  <small>
                    {events.length} record{events.length === 1 ? '' : 's'}
                    <span className="calendar-list-date-dots">
                      {roomDots.map((meta) => <i key={meta.index} style={{ backgroundColor: meta.color }} title={meta.shortLabel} />)}
                    </span>
                  </small>
                </div>
                <ChevronDown className={isOpen ? 'is-open' : ''} size={20} />
              </button>
              {isOpen && (
                <div className="calendar-list-records">
                  {events.map((event) => {
                    const meta = stayMeta(rows, event.itemId);
                    return (
                      <a className={`calendar-list-record calendar-list-record--${eventTone(event)}`} href={event.adminUrl} key={event.id} style={{ '--room-color': meta?.color || '#6750a4', '--room-bg': meta?.bgColor || '#eaddff' } as CSSProperties}>
                        <i />
                        <span title={meta?.displayName || event.itemName}>{meta?.shortLabel || event.itemName || event.type}</span>
                        <strong>{event.title}</strong>
                        <em>{event.rangeLabel}</em>
                        <small>{event.guestLabel || event.status || event.type}</small>
                      </a>
                    );
                  })}
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function CalendarRoomsView({
  rows,
  view,
  focusDate,
  globalSearch,
  visibleDays,
}: {
  rows: StayRowWithMeta[];
  view: OpsCalendarViewMode;
  focusDate: string;
  globalSearch: string;
  visibleDays: OpsCalendarDay[];
}) {
  const globalQuery = globalSearch.trim().toLowerCase();
  const displayRows = useMemo(() => {
    if (!globalQuery) return rows;
    return rows.filter(({ row, meta }) => (
      [meta.shortLabel, meta.displayName, meta.unitLabel, row.stay.subtitle].some((value) => value.toLowerCase().includes(globalQuery))
      || row.events.some((event) => eventMatchesQuery(event, globalQuery, meta))
    ));
  }, [globalQuery, rows]);
  const [selectedStay, setSelectedStay] = useState(rows[0]?.row.stay.id || 0);
  const active = displayRows.find(({ row }) => row.stay.id === selectedStay) || displayRows[0];
  const periodDays = useMemo(() => fallbackVisibleDays(rows, view, focusDate, visibleDays), [focusDate, rows, view, visibleDays]);
  const periodDates = useMemo(() => periodDays.map((day) => day.date), [periodDays]);
  const focusEvents = active ? active.row.events.filter((event) => eventCoversDay(event, focusDate)) : [];
  const periodEvents = active ? active.row.events.filter((event) => eventOverlapsDates(event, periodDates)) : [];
  const reservations = periodEvents.filter((event) => event.type === 'reservation');
  const blocks = periodEvents.filter((event) => event.type === 'block');
  const prices = periodEvents.filter((event) => event.type === 'price');

  useEffect(() => {
    if (displayRows.length > 0 && !displayRows.some(({ row }) => row.stay.id === selectedStay)) {
      setSelectedStay(displayRows[0].row.stay.id);
    }
  }, [displayRows, selectedStay]);

  if (!active) return <EmptyCalendarState title="No stays match" body="Change search or reset filters to view stay details." />;

  return (
    <section className="calendar-subview calendar-rooms-view">
      <aside className="calendar-rooms-list">
        <div>
          <strong>Stays</strong>
          <button type="button" aria-label="Add stay"><Sparkles size={18} /></button>
        </div>
        {displayRows.map(({ row, meta }) => {
          const roomPeriodEvents = row.events.filter((event) => eventOverlapsDates(event, periodDates));
          const roomReservations = roomPeriodEvents.filter((event) => event.type === 'reservation').length;
          const roomBlocks = roomPeriodEvents.filter((event) => event.type === 'block').length;
          const total = Math.max(periodDates.length, 1);
          return (
            <button
              className={active.row.stay.id === row.stay.id ? 'is-active' : ''}
              key={row.stay.id}
              type="button"
              onClick={() => setSelectedStay(row.stay.id)}
              style={{ '--room-color': meta.color, '--room-bg': meta.bgColor } as CSSProperties}
            >
              <span><Building2 size={18} /></span>
              <div>
                <strong>{meta.displayName}</strong>
                <small>{meta.capacityLabel} · {roomReservations} bookings</small>
                <i><b style={{ width: `${Math.min(((roomReservations + roomBlocks) / total) * 100, 100)}%` }} /></i>
              </div>
              <em>{Math.round(Math.min(((roomReservations + roomBlocks) / total) * 100, 100))}%</em>
            </button>
          );
        })}
        <footer>
          <p>Calendar status</p>
          <span><i className="is-booked" /> Booked</span>
          <span><i className="is-available" /> Available</span>
        </footer>
      </aside>

      <div className="calendar-room-detail">
        <article className="calendar-room-hero" style={{ '--room-color': active.meta.color, '--room-bg': active.meta.bgColor } as CSSProperties}>
          <div>
            <span><Building2 size={22} /> Stay Details</span>
            <h2>{active.meta.displayName}</h2>
            <p>{cleanCalendarSubtitle(active.row.stay.subtitle)}</p>
            <small><Users size={18} /> {active.meta.capacityLabel}</small>
          </div>
          <strong>{active.row.stay.feedStatus}</strong>
        </article>

        <div className="calendar-room-metrics">
          <MetricTile color="#6750a4" icon={<CalendarDays size={20} />} label="Reservations" value={reservations.length} />
          <MetricTile color="#b3261e" icon={<AlertCircle size={20} />} label="Blocks" value={blocks.length} />
          <MetricTile color="#c25100" icon={<DollarSign size={20} />} label="Price overrides" value={prices.length} />
        </div>

        <section className="calendar-room-amenities">
          <h3>Calendar setup</h3>
          <span>{active.row.stay.defaultPrice} default</span>
          <span>{cleanCalendarSubtitle(active.row.stay.feedLabel)}</span>
          <span>{active.row.stay.isConfigured ? 'Feed connected' : 'Feed needs setup'}</span>
          <span>{active.row.stay.lastCheckedAt ? `Last checked ${compactDate(active.row.stay.lastCheckedAt.slice(0, 10))}` : 'No feed check yet'}</span>
        </section>

        <section className="calendar-room-schedule">
          <h3>{view === 'list' ? 'Day Schedule' : `${periodTitle(view)} Schedule`} <span>{periodLabel(view, focusDate, periodDays)}</span></h3>
          {timeSlots.map((slot) => {
            const unavailable = focusEvents[0];
            return (
              <article className={unavailable ? 'is-booked' : 'is-free'} key={slot}>
                <Clock3 size={17} />
                <strong>{slot}</strong>
                {unavailable ? (
                  <>
                    <AlertCircle size={17} />
                    <span>{unavailable.title}</span>
                    <em>{unavailable.type}</em>
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={17} />
                    <span>Available</span>
                    <em>Free</em>
                  </>
                )}
              </article>
            );
          })}
        </section>
      </div>
    </section>
  );
}

export function CalendarAnalyticsView({
  rows,
  focusDate,
  view,
  globalSearch,
  visibleDays,
}: {
  rows: StayRowWithMeta[];
  focusDate: string;
  view: OpsCalendarViewMode;
  globalSearch: string;
  visibleDays: OpsCalendarDay[];
}) {
  const globalQuery = globalSearch.trim().toLowerCase();
  const events = useMemo(() => uniqueEvents(rows).filter((event) => eventMatchesQuery(event, globalQuery, stayMeta(rows, event.itemId))), [globalQuery, rows]);
  const periodDays = useMemo(() => fallbackVisibleDays(rows, view, focusDate, visibleDays), [focusDate, rows, view, visibleDays]);
  const periodDates = useMemo(() => periodDays.map((day) => day.date), [periodDays]);
  const periodEvents = events.filter((event) => eventOverlapsDates(event, periodDates));
  const reservationEvents = periodEvents.filter((event) => event.type === 'reservation');
  const monthDays = useMemo(() => fallbackVisibleDays(rows, 'month', focusDate, []), [focusDate, rows]);
  const weekDays = useMemo(() => fallbackVisibleDays(rows, 'week', focusDate, []), [focusDate, rows]);
  const selectedDay = useMemo(() => fallbackVisibleDays(rows, 'list', focusDate, []), [focusDate, rows]);
  const reservationCountFor = (days: OpsCalendarDay[]) => {
    const dates = days.map((day) => day.date);
    return events.filter((event) => event.type === 'reservation' && eventOverlapsDates(event, dates)).length;
  };
  const stayCounts = rows.map(({ row, meta }) => ({
    id: row.stay.id,
    name: meta.displayName,
    shortLabel: meta.shortLabel,
    color: meta.color,
    bgColor: meta.bgColor,
    count: row.events.filter((event) => event.type === 'reservation' && eventOverlapsDates(event, periodDates) && eventMatchesQuery(event, globalQuery, meta)).length,
  }));
  const maxStayCount = Math.max(...stayCounts.map((stay) => stay.count), 1);
  const dailyCounts = periodDays.map((day) => ({
    day,
    count: reservationEvents.filter((event) => listEntryDate(event, periodDates) === day.date).length,
  }));
  const maxDailyCount = Math.max(...dailyCounts.map((day) => day.count), 1);
  const topGuests = Object.entries(reservationEvents.reduce<Record<string, number>>((acc, event) => {
    const name = event.title || 'Guest reservation';
    acc[name] = (acc[name] || 0) + 1;
    return acc;
  }, {})).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const mostBooked = stayCounts.reduce((winner, stay) => (stay.count > winner.count ? stay : winner), stayCounts[0] || { shortLabel: '-', count: 0 });
  const hasMostBooked = Boolean(mostBooked?.count);

  return (
    <section className="calendar-subview calendar-analytics-view">
      <div className="calendar-analytics-kpis">
        <MetricTile color="#6750a4" icon={<CalendarDays size={22} />} label="This Month" value={reservationCountFor(monthDays)} caption={periodLabel('month', focusDate, monthDays)} />
        <MetricTile color="#0072b8" icon={<TrendingUp size={22} />} label="This Week" value={reservationCountFor(weekDays)} caption={periodLabel('week', focusDate, weekDays)} />
        <MetricTile color="#7d5260" icon={<Clock3 size={22} />} label="Selected Day" value={reservationCountFor(selectedDay)} caption={periodLabel('list', focusDate, selectedDay)} />
        <MetricTile color="#c25100" icon={<Building2 size={22} />} label="Most Booked" value={hasMostBooked ? mostBooked.shortLabel : '-'} caption={hasMostBooked ? `${mostBooked.count} bookings` : 'No bookings'} />
        <MetricTile color="#087927" icon={<Users size={22} />} label="Total Stays" value={rows.length} caption={`${events.length} calendar records`} />
      </div>

      <div className="calendar-analytics-grid">
        <article className="calendar-analytics-card calendar-analytics-card--wide">
          <h3>Daily Bookings — {periodLabel(view, focusDate, periodDays)}</h3>
          <div className="calendar-line-chart" style={{ '--analytics-day-count': Math.max(dailyCounts.length, 1), '--max-count': maxDailyCount } as CSSProperties}>
            {dailyCounts.map(({ day, count }) => (
              <span className={day.isToday ? 'is-today' : ''} key={day.date} style={{ '--bar-height': `${Math.max((count / maxDailyCount) * 100, count ? 8 : 2)}%` } as CSSProperties}>
                <i />
                <small>{day.day}</small>
              </span>
            ))}
          </div>
        </article>

        <article className="calendar-analytics-card">
          <h3>Record Mix</h3>
          <div className="calendar-donut">
            <strong>{periodEvents.length}</strong>
            <span>records</span>
          </div>
          <div className="calendar-donut-legend">
            <span><i className="is-booked" /> {reservationEvents.length} reservations</span>
            <span><i className="is-blocked" /> {periodEvents.filter((event) => event.type === 'block').length} blocks</span>
            <span><i className="is-priced" /> {periodEvents.filter((event) => event.type === 'price').length} prices</span>
          </div>
        </article>

        <article className="calendar-analytics-card">
          <h3>Bookings by Stay</h3>
          <div className="calendar-bar-list">
            {stayCounts.map((stay) => (
              <div key={stay.id}>
                <span>{stay.shortLabel}</span>
                <i><b style={{ width: `${(stay.count / maxStayCount) * 100}%`, backgroundColor: stay.color }} /></i>
                <strong>{stay.count}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="calendar-analytics-card">
          <h3>Top Guests</h3>
          {topGuests.length === 0 ? <p>No guest reservations in this period.</p> : (
            <div className="calendar-top-guests">
              {topGuests.map(([name, count], index) => (
                <div key={name}>
                  <span>{index + 1}</span>
                  <strong>{name}</strong>
                  <em>{count}</em>
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}

function MetricTile({
  color,
  icon,
  label,
  value,
  caption,
}: {
  color: string;
  icon: ReactNode;
  label: string;
  value: string | number;
  caption?: string;
}) {
  return (
    <article className="calendar-metric-tile" style={{ '--metric-color': color } as CSSProperties}>
      <div>
        <span>{label}</span>
        {icon}
      </div>
      <strong>{value}</strong>
      {caption && <small>{caption}</small>}
    </article>
  );
}

function EmptyCalendarState({ title, body }: { title: string; body: string }) {
  return (
    <article className="calendar-empty-state">
      <CalendarDays size={44} />
      <h3>{title}</h3>
      <p>{body}</p>
    </article>
  );
}
