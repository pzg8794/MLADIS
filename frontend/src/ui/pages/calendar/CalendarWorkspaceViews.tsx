import { CSSProperties, ReactNode, useMemo, useState } from 'react';
import {
  AlertCircle,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  DollarSign,
  Search,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react';
import {
  CalendarEventKind,
  CalendarTimeFilter,
  CalendarWorkspace,
  CalendarWorkspaceRowProjection,
  calendarTodayIso,
  cleanCalendarSubtitle,
  compactDate,
  dateFromIso,
  fullDate,
  periodLabel,
  periodTitle,
} from '../../../domain/calendar';
import { OpsCalendarDay, OpsCalendarEvent, OpsCalendarViewMode } from '../../../domain/models';

type StayRowWithMeta = CalendarWorkspaceRowProjection;

function eventTone(event: OpsCalendarEvent) {
  if (event.type === 'reservation') return 'reservation';
  if (event.type === 'block') return 'block';
  return 'price';
}

export function CalendarListView({
  workspace,
  rows,
  view,
  focusDate,
  globalSearch,
  visibleDays,
}: {
  workspace: CalendarWorkspace;
  rows: StayRowWithMeta[];
  view: OpsCalendarViewMode;
  focusDate: string;
  globalSearch: string;
  visibleDays: OpsCalendarDay[];
}) {
  const [search, setSearch] = useState('');
  const [stayFilter, setStayFilter] = useState<number | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<CalendarEventKind>('all');
  const [timeFilter, setTimeFilter] = useState<CalendarTimeFilter>('all');
  const projection = useMemo(() => workspace.listProjection(rows, view, focusDate, visibleDays, {
    search,
    globalSearch,
    stayFilter,
    typeFilter,
    timeFilter,
  }), [focusDate, globalSearch, rows, search, stayFilter, timeFilter, typeFilter, view, visibleDays, workspace]);
  const { periodDays, periodDates, filteredEvents, grouped } = projection;
  const [expandedDateState, setExpandedDate] = useState<string | null>(null);
  const expandedDate = expandedDateState && periodDates.includes(expandedDateState) ? expandedDateState : null;

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
          {(['all', 'today', 'upcoming', 'past'] as CalendarTimeFilter[]).map((kind) => (
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
        ) : grouped.map(({ date, events, roomDots }) => {
          const isOpen = expandedDate === date;
          return (
            <article className="calendar-list-date-group" key={date}>
              <button type="button" onClick={() => setExpandedDate(isOpen ? null : date)}>
                <span className={date === calendarTodayIso() ? 'is-today' : ''}>
                  <b>{new Intl.DateTimeFormat('en-US', { weekday: 'short' }).format(dateFromIso(date))}</b>
                  <strong>{dateFromIso(date).getDate()}</strong>
                </span>
                <div>
                  <strong>{date === calendarTodayIso() ? 'Today · ' : ''}{fullDate(date)}</strong>
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
                  {events.map(({ event, meta }) => {
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
  workspace,
  rows,
  view,
  focusDate,
  globalSearch,
  visibleDays,
}: {
  workspace: CalendarWorkspace;
  rows: StayRowWithMeta[];
  view: OpsCalendarViewMode;
  focusDate: string;
  globalSearch: string;
  visibleDays: OpsCalendarDay[];
}) {
  const [selectedStayId, setSelectedStay] = useState(rows[0]?.row.stay.id || 0);
  const projection = useMemo(
    () => workspace.roomsProjection(rows, view, focusDate, visibleDays, globalSearch, selectedStayId),
    [focusDate, globalSearch, rows, selectedStayId, view, visibleDays, workspace],
  );
  const { active, periodDays, reservations, blocks, prices, rowSummaries, scheduleSlots } = projection;

  if (!active) return <EmptyCalendarState title="No stays match" body="Change search or reset filters to view stay details." />;

  return (
    <section className="calendar-subview calendar-rooms-view">
      <aside className="calendar-rooms-list">
        <div>
          <strong>Stays</strong>
          <button type="button" aria-label="Add stay"><Sparkles size={18} /></button>
        </div>
        {rowSummaries.map(({ projection: { row, meta }, roomReservations, occupiedPercent }) => {
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
                <i><b style={{ width: `${occupiedPercent}%` }} /></i>
              </div>
              <em>{occupiedPercent}%</em>
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
          {scheduleSlots.map(({ slot, event: unavailable }) => {
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
  workspace,
  rows,
  focusDate,
  view,
  globalSearch,
  visibleDays,
}: {
  workspace: CalendarWorkspace;
  rows: StayRowWithMeta[];
  focusDate: string;
  view: OpsCalendarViewMode;
  globalSearch: string;
  visibleDays: OpsCalendarDay[];
}) {
  const projection = useMemo(
    () => workspace.analyticsProjection(rows, focusDate, view, visibleDays, globalSearch),
    [focusDate, globalSearch, rows, view, visibleDays, workspace],
  );
  const {
    events,
    periodDays,
    periodEvents,
    monthDays,
    weekDays,
    selectedDay,
    monthReservationCount,
    weekReservationCount,
    selectedDayReservationCount,
    stayCounts,
    maxStayCount,
    dailyCounts,
    maxDailyCount,
    topGuests,
    mostBooked,
    hasMostBooked,
    recordMix,
  } = projection;

  return (
    <section className="calendar-subview calendar-analytics-view">
      <div className="calendar-analytics-kpis">
        <MetricTile color="#0d7fa1" icon={<CalendarDays size={18} />} label="This Month" value={monthReservationCount} caption={periodLabel('month', focusDate, monthDays)} />
        <MetricTile color="#2563eb" icon={<TrendingUp size={18} />} label="This Week" value={weekReservationCount} caption={periodLabel('week', focusDate, weekDays)} />
        <MetricTile color="#475569" icon={<Clock3 size={18} />} label="Selected Day" value={selectedDayReservationCount} caption={periodLabel('list', focusDate, selectedDay)} />
        <MetricTile color="#ea580c" icon={<Building2 size={18} />} label="Most Booked" value={hasMostBooked && mostBooked ? mostBooked.shortLabel : '-'} caption={hasMostBooked && mostBooked ? `${mostBooked.count} bookings` : 'No bookings'} />
        <MetricTile color="#16a34a" icon={<Users size={18} />} label="Total Stays" value={rows.length} caption={`${events.length} calendar records`} />
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
            <span><i className="is-booked" /> {recordMix.reservations} reservations</span>
            <span><i className="is-blocked" /> {recordMix.blocks} blocks</span>
            <span><i className="is-priced" /> {recordMix.prices} prices</span>
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
              {topGuests.map(({ name, count }, index) => (
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
