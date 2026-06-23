import type {
  OpsCalendarDay,
  OpsCalendarEvent,
  OpsCalendarSnapshot,
  OpsCalendarStayRow,
  OpsCalendarViewMode,
} from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type CalendarStayFilterId = 'all' | number;

export type CalendarRange = {
  start: string;
  end: string;
};

export type CalendarGridCellPosition = {
  rowIndex: number;
  colIndex: number;
};

export type CalendarStayVisualMeta = {
  index: number;
  color: string;
  bgColor: string;
  textColor: string;
  shortLabel: string;
  displayName: string;
  unitLabel: string;
  capacityLabel: string;
  isDemo: boolean;
};

export type CalendarWorkspaceRowProjection = {
  row: OpsCalendarStayRow;
  meta: CalendarStayVisualMeta;
};

export type CalendarWorkspaceFilters = {
  activeStayFilters?: ReadonlySet<CalendarStayFilterId> | CalendarStayFilterId[];
  search?: string;
};

export type CalendarSelectionProjection = {
  rows: CalendarWorkspaceRowProjection[];
  dates: OpsCalendarDay[];
};

export type CalendarPeriodAnalytics = {
  days: OpsCalendarDay[];
  dates: string[];
  events: OpsCalendarEvent[];
  reservations: OpsCalendarEvent[];
  blocks: OpsCalendarEvent[];
  priceOverrides: OpsCalendarEvent[];
};

export type CalendarEventKind = 'all' | 'reservation' | 'block' | 'price';

export type CalendarTimeFilter = 'all' | 'today' | 'upcoming' | 'past';

export type CalendarListProjectionFilters = {
  search?: string;
  globalSearch?: string;
  stayFilter?: CalendarStayFilterId;
  typeFilter?: CalendarEventKind;
  timeFilter?: CalendarTimeFilter;
};

export type CalendarListDateGroupProjection = {
  date: string;
  events: Array<{
    event: OpsCalendarEvent;
    meta?: CalendarStayVisualMeta;
  }>;
  roomDots: CalendarStayVisualMeta[];
};

export type CalendarListProjection = {
  periodDays: OpsCalendarDay[];
  periodDates: string[];
  filteredEvents: OpsCalendarEvent[];
  grouped: CalendarListDateGroupProjection[];
};

export type CalendarRoomRowSummaryProjection = {
  projection: CalendarWorkspaceRowProjection;
  roomReservations: number;
  roomBlocks: number;
  occupiedPercent: number;
};

export type CalendarRoomScheduleSlotProjection = {
  slot: string;
  event: OpsCalendarEvent | null;
  isAvailable: boolean;
};

export type CalendarRoomProjection = {
  displayRows: CalendarWorkspaceRowProjection[];
  active: CalendarWorkspaceRowProjection | null;
  selectedStayId: number;
  periodDays: OpsCalendarDay[];
  periodDates: string[];
  focusEvents: OpsCalendarEvent[];
  periodEvents: OpsCalendarEvent[];
  reservations: OpsCalendarEvent[];
  blocks: OpsCalendarEvent[];
  prices: OpsCalendarEvent[];
  rowSummaries: CalendarRoomRowSummaryProjection[];
  scheduleSlots: CalendarRoomScheduleSlotProjection[];
};

export type CalendarStayCountProjection = {
  id: number;
  name: string;
  shortLabel: string;
  color: string;
  bgColor: string;
  count: number;
};

export type CalendarDailyCountProjection = {
  day: OpsCalendarDay;
  count: number;
};

export type CalendarTopGuestProjection = {
  name: string;
  count: number;
};

export type CalendarAnalyticsProjection = {
  events: OpsCalendarEvent[];
  periodDays: OpsCalendarDay[];
  periodDates: string[];
  periodEvents: OpsCalendarEvent[];
  reservationEvents: OpsCalendarEvent[];
  monthDays: OpsCalendarDay[];
  weekDays: OpsCalendarDay[];
  selectedDay: OpsCalendarDay[];
  monthReservationCount: number;
  weekReservationCount: number;
  selectedDayReservationCount: number;
  stayCounts: CalendarStayCountProjection[];
  maxStayCount: number;
  dailyCounts: CalendarDailyCountProjection[];
  maxDailyCount: number;
  topGuests: CalendarTopGuestProjection[];
  mostBooked: CalendarStayCountProjection | null;
  hasMostBooked: boolean;
  recordMix: {
    reservations: number;
    blocks: number;
    prices: number;
  };
};

export const calendarDefaultTimeSlots = [
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

const roomPalette = [
  { color: '#0d7fa1', bgColor: '#e5f6fb', textColor: '#073042' },
  { color: '#2563eb', bgColor: '#eaf2ff', textColor: '#172554' },
  { color: '#ea580c', bgColor: '#fff1e7', textColor: '#431407' },
  { color: '#16a34a', bgColor: '#e9f9ef', textColor: '#052e16' },
  { color: '#7c3aed', bgColor: '#f3ecff', textColor: '#2e1065' },
  { color: '#475569', bgColor: '#f1f5f9', textColor: '#0f172a' },
];

export function calendarTodayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function dateFromIso(value: string) {
  return new Date(`${value}T00:00:00`);
}

export function compactDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dateFromIso(value));
}

export function longDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).format(dateFromIso(value));
}

export function fullDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(dateFromIso(value));
}

export function monthKey(value: string) {
  return value.slice(0, 7);
}

export function monthLabel(value: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(dateFromIso(`${monthKey(value)}-01`));
}

export function shortPeriodDate(value: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dateFromIso(value));
}

export function sortedRange(first: string, second: string): CalendarRange {
  return first <= second ? { start: first, end: second } : { start: second, end: first };
}

export function emptyRange(focusDate: string): CalendarRange {
  return { start: focusDate, end: focusDate };
}

export function rangeLabel(range: CalendarRange) {
  if (!range.start) return 'Select dates on the calendar';
  if (!range.end || range.start === range.end) return longDate(range.start);
  return `${compactDate(range.start)} - ${compactDate(range.end)}`;
}

export function dateRangeLabel(days: OpsCalendarDay[]) {
  if (days.length === 0) return '';
  if (days.length === 1) return fullDate(days[0].date);
  return `${compactDate(days[0].date)} - ${compactDate(days[days.length - 1].date)}, ${dateFromIso(days[days.length - 1].date).getFullYear()} (${days.length} days)`;
}

export function periodLabel(view: OpsCalendarViewMode, focusDate: string, days: OpsCalendarDay[]) {
  if (view === 'month') return monthLabel(focusDate);
  if (days.length === 0) return fullDate(focusDate);
  if (view === 'list') return fullDate(days[0].date);
  return `${shortPeriodDate(days[0].date)} - ${shortPeriodDate(days[days.length - 1].date)}, ${dateFromIso(days[days.length - 1].date).getFullYear()}`;
}

export function eventCoversDay(event: OpsCalendarEvent, date: string) {
  if (event.type === 'reservation') {
    return event.start <= date && date < event.end;
  }
  return event.start <= date && date <= event.end;
}

export function calendarEventTone(event: OpsCalendarEvent) {
  if (event.type === 'reservation') return 'booking';
  if (event.type === 'block') return 'block';
  return 'price';
}

export function eventLabel(event: OpsCalendarEvent) {
  if (event.type === 'reservation') return event.guestLabel || 'Reservation';
  if (event.type === 'block') return 'Blocked';
  return event.amount || 'Price';
}

export function isWeekendIso(value: string) {
  const day = dateFromIso(value).getDay();
  return day === 0 || day === 6;
}

export function calendarRowDays(row: OpsCalendarStayRow, mode: OpsCalendarViewMode, focusDate: string) {
  if (mode === 'month') return row.weeks.flat();
  if (mode === 'week') return row.weekDays;
  const allDays = row.weeks.flat();
  return allDays.filter((day) => day.date === focusDate);
}

export function daysForWeekendPreference(days: OpsCalendarDay[], showWeekends: boolean) {
  return showWeekends ? days : days.filter((day) => !isWeekendIso(day.date));
}

export function selectedGridCoversCell(start: CalendarGridCellPosition | null, end: CalendarGridCellPosition | null, rowIndex: number, colIndex: number) {
  if (!start || !end) return false;
  const rowStart = Math.min(start.rowIndex, end.rowIndex);
  const rowEnd = Math.max(start.rowIndex, end.rowIndex);
  const colStart = Math.min(start.colIndex, end.colIndex);
  const colEnd = Math.max(start.colIndex, end.colIndex);
  return rowIndex >= rowStart && rowIndex <= rowEnd && colIndex >= colStart && colIndex <= colEnd;
}

export function eventOverlapsDates(event: OpsCalendarEvent, dates: string[]) {
  return dates.some((date) => eventCoversDay(event, date));
}

export function listEntryDate(event: OpsCalendarEvent, dates: string[]) {
  if (dates.includes(event.start)) return event.start;
  return dates.find((date) => eventCoversDay(event, date)) || event.start;
}

export function isFutureOrToday(value: string) {
  return value >= calendarTodayIso();
}

export function isPast(value: string) {
  return value < calendarTodayIso();
}

export function firstMonthDays(rows: CalendarWorkspaceRowProjection[]) {
  const days = rows[0]?.row.weeks.flat() || [];
  const seen = new Map<string, OpsCalendarDay>();
  days.filter((day) => day.inMonth).forEach((day) => seen.set(day.date, day));
  return Array.from(seen.values());
}

export function fallbackVisibleDays(rows: CalendarWorkspaceRowProjection[], view: OpsCalendarViewMode, focusDate: string, visibleDays: OpsCalendarDay[]) {
  const firstRow = rows[0]?.row;
  if (!firstRow) return [];
  if (view === 'month') return firstMonthDays(rows);
  if (visibleDays.length > 0) return visibleDays;
  if (view === 'week') return firstRow.weekDays;
  return firstRow.weeks.flat().filter((day) => day.date === focusDate);
}

export function cleanCalendarSubtitle(value?: string) {
  return (value || 'Direct booking calendar')
    .replace(/^MLADIS\s*[-–—]\s*/i, '')
    .replace(/\bBedrooms?\b/gi, 'Beds')
    .replace(/\s+/g, ' ')
    .trim();
}

export function periodTitle(view: OpsCalendarViewMode) {
  if (view === 'month') return 'This Month';
  if (view === 'week') return 'This Week';
  return 'Selected Day';
}

export function uniqueEvents(rows: CalendarWorkspaceRowProjection[]) {
  const seen = new Map<string, OpsCalendarEvent>();
  rows.forEach(({ row }) => row.events.forEach((event) => seen.set(event.id, event)));
  return Array.from(seen.values()).sort((a, b) => a.start.localeCompare(b.start) || a.title.localeCompare(b.title));
}

export function stayMeta(rows: CalendarWorkspaceRowProjection[], itemId: number) {
  return rows.find(({ row }) => row.stay.id === itemId)?.meta;
}

export function eventMatchesQuery(event: OpsCalendarEvent, query: string, meta?: CalendarStayVisualMeta) {
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

function lockedStayIdentity(name: string, subtitle: string, fallback: number) {
  const cleaned = name
    .replace(/^MLADIS\s*[-–—]\s*/i, '')
    .replace(/\bBedrooms?\b/gi, 'Beds')
    .replace(/\s+/g, ' ')
    .trim();
  const isDemoStay = /\bdemo\b|browser walkthrough/i.test(`${cleaned} ${subtitle}`);
  const unitMatch = cleaned.match(/\b([A-Z])[-\s]?(\d{3})\b/i);
  const bedCount = cleaned.match(/(\d+)\s*(?:bedrooms?|beds?)\b/i)?.[1];
  const isCombinedStay = !unitMatch && bedCount === '6';
  const block = (unitMatch?.[1] || 'G').toUpperCase();
  const number = unitMatch?.[2] || (isCombinedStay ? 'All' : String(101 + (fallback % 2)));
  const unitLabel = `${block}-${number}`;
  const propertyType = isCombinedStay || number === 'All' ? 'Apts' : 'Apt';
  const shortLabel = number === 'All' ? `APTs-${unitLabel}` : `APT-${unitLabel}`;
  const bedsLabel = bedCount ? `${bedCount} Bed${bedCount === '1' ? '' : 's'}` : 'Stay';
  const capacityLabel = bedCount ? bedsLabel : (subtitle || 'Stay calendar');
  const title = cleaned
    .replace(/\b[A-Z][-\s]?\d{3}\b/gi, '')
    .replace(/\(?\bapartments?\b\)?/gi, '')
    .replace(/\b\d+\s*(?:bedrooms?|beds?)\b/gi, '')
    .replace(/^MLADIS\s*[-–—]\s*/i, '')
    .replace(/\s*[-–—]\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .trim() || 'Vacation Home & Pool';

  if (isDemoStay && !unitMatch && !isCombinedStay) {
    return {
      unitLabel: 'Demo',
      shortLabel: 'Demo',
      displayName: `Demo Stay - ${title}`,
      capacityLabel: subtitle || 'Demo stay',
      isDemo: true,
    };
  }

  return {
    unitLabel,
    shortLabel,
    displayName: `${bedsLabel} ${propertyType} - ${title} - ${unitLabel}`,
    capacityLabel,
    isDemo: false,
  };
}

function visualMetaForRow(row: OpsCalendarStayRow, index: number): CalendarStayVisualMeta {
  const tone = roomPalette[index % roomPalette.length];
  const identity = lockedStayIdentity(row.stay.name, row.stay.subtitle, index);
  return {
    ...tone,
    index,
    ...identity,
  };
}

function activeFilterSet(filters?: ReadonlySet<CalendarStayFilterId> | CalendarStayFilterId[]) {
  if (!filters) return new Set<CalendarStayFilterId>(['all']);
  return filters instanceof Set ? filters : new Set(filters);
}

function rowMatchesSearch({ row, meta }: CalendarWorkspaceRowProjection, query: string) {
  if (!query) return true;
  return [
    row.stay.name,
    row.stay.subtitle,
    meta.shortLabel,
    meta.displayName,
    meta.unitLabel,
    ...row.events.flatMap((event) => [
      event.title,
      event.subtitle,
      event.itemName,
      event.guestLabel,
      event.rangeLabel,
    ]),
  ].some((value) => value.toLowerCase().includes(query));
}

function matchesCalendarTimeFilter(event: OpsCalendarEvent, filter: CalendarTimeFilter) {
  if (filter === 'all') return true;
  if (filter === 'today') return event.start <= calendarTodayIso() && event.end >= calendarTodayIso();
  if (filter === 'upcoming') return isFutureOrToday(event.start);
  return isPast(event.end);
}

function countReservationsForDays(events: OpsCalendarEvent[], days: OpsCalendarDay[]) {
  const dates = days.map((day) => day.date);
  return events.filter((event) => event.type === 'reservation' && eventOverlapsDates(event, dates)).length;
}

export class CalendarWorkspace {
  constructor(
    public readonly snapshot: OpsCalendarSnapshot,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}

  rowProjections() {
    return this.snapshot.stayRows
      .map((row, index) => ({ row, meta: visualMetaForRow(row, index) }))
      .filter(({ meta }) => !meta.isDemo);
  }

  visibleRows(filters: CalendarWorkspaceFilters = {}) {
    const filterSet = activeFilterSet(filters.activeStayFilters);
    const query = (filters.search || '').trim().toLowerCase();
    return this.rowProjections().filter((projection) => {
      const matchesActiveFilter = filterSet.has('all') || filterSet.has(projection.row.stay.id);
      return matchesActiveFilter && rowMatchesSearch(projection, query);
    });
  }

  filteredEvents(filters: CalendarWorkspaceFilters = {}) {
    const rows = this.rowProjections();
    const filterSet = activeFilterSet(filters.activeStayFilters);
    const query = (filters.search || '').trim().toLowerCase();
    return uniqueEvents(rows).filter((event) => {
      const inFilter = filterSet.has('all') || filterSet.has(event.itemId);
      return inFilter && eventMatchesQuery(event, query, stayMeta(rows, event.itemId));
    });
  }

  reservationCount(filters: CalendarWorkspaceFilters = {}) {
    return this.filteredEvents(filters).filter((event) => event.type === 'reservation').length;
  }

  periodDays(view: OpsCalendarViewMode, focusDate: string, showWeekends: boolean, row?: OpsCalendarStayRow) {
    const sourceRow = row || this.visibleRows()[0]?.row;
    const days = sourceRow ? calendarRowDays(sourceRow, view, focusDate) : [];
    return daysForWeekendPreference(days, showWeekends);
  }

  selectionFromCells(
    rows: CalendarWorkspaceRowProjection[],
    view: OpsCalendarViewMode,
    focusDate: string,
    showWeekends: boolean,
    start: CalendarGridCellPosition,
    end: CalendarGridCellPosition,
  ): CalendarSelectionProjection {
    const rowStart = Math.min(start.rowIndex, end.rowIndex);
    const rowEnd = Math.max(start.rowIndex, end.rowIndex);
    const colStart = Math.min(start.colIndex, end.colIndex);
    const colEnd = Math.max(start.colIndex, end.colIndex);
    const selectedRows = rows.slice(rowStart, rowEnd + 1);
    const firstRow = rows[0]?.row;
    const days = firstRow
      ? daysForWeekendPreference(calendarRowDays(firstRow, view, focusDate), showWeekends).slice(colStart, colEnd + 1)
      : [];
    return { rows: selectedRows, dates: days };
  }

  listProjection(
    rows: CalendarWorkspaceRowProjection[],
    view: OpsCalendarViewMode,
    focusDate: string,
    visibleDays: OpsCalendarDay[],
    filters: CalendarListProjectionFilters = {},
  ): CalendarListProjection {
    const periodDays = fallbackVisibleDays(rows, view, focusDate, visibleDays);
    const periodDates = periodDays.map((day) => day.date);
    const query = (filters.search || '').trim().toLowerCase();
    const globalQuery = (filters.globalSearch || '').trim().toLowerCase();
    const stayFilter = filters.stayFilter ?? 'all';
    const typeFilter = filters.typeFilter ?? 'all';
    const timeFilter = filters.timeFilter ?? 'all';

    const filteredEvents = uniqueEvents(rows).filter((event) => {
      const meta = stayMeta(rows, event.itemId);
      const matchesStay = stayFilter === 'all' || event.itemId === stayFilter;
      const matchesType = typeFilter === 'all' || event.type === typeFilter;
      const matchesPeriod = eventOverlapsDates(event, periodDates);
      return (
        matchesStay
        && matchesType
        && matchesPeriod
        && matchesCalendarTimeFilter(event, timeFilter)
        && eventMatchesQuery(event, query, meta)
        && eventMatchesQuery(event, globalQuery, meta)
      );
    });

    const map = new Map<string, OpsCalendarEvent[]>();
    filteredEvents.forEach((event) => {
      const date = listEntryDate(event, periodDates);
      if (!map.has(date)) map.set(date, []);
      map.get(date)?.push(event);
    });

    const grouped = Array.from(map.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, events]) => ({
        date,
        events: events.map((event) => ({ event, meta: stayMeta(rows, event.itemId) })),
        roomDots: Array.from(new Set(events.map((event) => event.itemId)))
          .map((itemId) => stayMeta(rows, itemId))
          .filter(Boolean) as CalendarStayVisualMeta[],
      }));

    return { periodDays, periodDates, filteredEvents, grouped };
  }

  roomsProjection(
    rows: CalendarWorkspaceRowProjection[],
    view: OpsCalendarViewMode,
    focusDate: string,
    visibleDays: OpsCalendarDay[],
    globalSearch = '',
    requestedStayId = 0,
  ): CalendarRoomProjection {
    const globalQuery = globalSearch.trim().toLowerCase();
    const displayRows = globalQuery
      ? rows.filter(({ row, meta }) => (
          [meta.shortLabel, meta.displayName, meta.unitLabel, row.stay.subtitle].some((value) => value.toLowerCase().includes(globalQuery))
          || row.events.some((event) => eventMatchesQuery(event, globalQuery, meta))
        ))
      : rows;
    const selectedStayId = displayRows.some(({ row }) => row.stay.id === requestedStayId)
      ? requestedStayId
      : displayRows[0]?.row.stay.id || 0;
    const active = displayRows.find(({ row }) => row.stay.id === selectedStayId) || displayRows[0] || null;
    const periodDays = fallbackVisibleDays(rows, view, focusDate, visibleDays);
    const periodDates = periodDays.map((day) => day.date);
    const focusEvents = active ? active.row.events.filter((event) => eventCoversDay(event, focusDate)) : [];
    const periodEvents = active ? active.row.events.filter((event) => eventOverlapsDates(event, periodDates)) : [];
    const reservations = periodEvents.filter((event) => event.type === 'reservation');
    const blocks = periodEvents.filter((event) => event.type === 'block');
    const prices = periodEvents.filter((event) => event.type === 'price');
    const totalDays = Math.max(periodDates.length, 1);
    const rowSummaries = displayRows.map((projection) => {
      const roomPeriodEvents = projection.row.events.filter((event) => eventOverlapsDates(event, periodDates));
      const roomReservations = roomPeriodEvents.filter((event) => event.type === 'reservation').length;
      const roomBlocks = roomPeriodEvents.filter((event) => event.type === 'block').length;
      return {
        projection,
        roomReservations,
        roomBlocks,
        occupiedPercent: Math.round(Math.min(((roomReservations + roomBlocks) / totalDays) * 100, 100)),
      };
    });
    const scheduleSlots = calendarDefaultTimeSlots.map((slot) => {
      const event = focusEvents[0] || null;
      return { slot, event, isAvailable: !event };
    });

    return {
      displayRows,
      active,
      selectedStayId,
      periodDays,
      periodDates,
      focusEvents,
      periodEvents,
      reservations,
      blocks,
      prices,
      rowSummaries,
      scheduleSlots,
    };
  }

  analyticsProjection(
    rows: CalendarWorkspaceRowProjection[],
    focusDate: string,
    view: OpsCalendarViewMode,
    visibleDays: OpsCalendarDay[],
    globalSearch = '',
  ): CalendarAnalyticsProjection {
    const globalQuery = globalSearch.trim().toLowerCase();
    const events = uniqueEvents(rows).filter((event) => eventMatchesQuery(event, globalQuery, stayMeta(rows, event.itemId)));
    const periodDays = fallbackVisibleDays(rows, view, focusDate, visibleDays);
    const periodDates = periodDays.map((day) => day.date);
    const periodEvents = events.filter((event) => eventOverlapsDates(event, periodDates));
    const reservationEvents = periodEvents.filter((event) => event.type === 'reservation');
    const monthDays = fallbackVisibleDays(rows, 'month', focusDate, []);
    const weekDays = fallbackVisibleDays(rows, 'week', focusDate, []);
    const selectedDay = fallbackVisibleDays(rows, 'list', focusDate, []);
    const stayCounts = rows.map(({ row, meta }) => ({
      id: row.stay.id,
      name: meta.displayName,
      shortLabel: meta.shortLabel,
      color: meta.color,
      bgColor: meta.bgColor,
      count: row.events.filter((event) => (
        event.type === 'reservation'
        && eventOverlapsDates(event, periodDates)
        && eventMatchesQuery(event, globalQuery, meta)
      )).length,
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
    }, {}))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }));
    const mostBooked = stayCounts.reduce<CalendarStayCountProjection | null>((winner, stay) => {
      if (!winner || stay.count > winner.count) return stay;
      return winner;
    }, null);

    return {
      events,
      periodDays,
      periodDates,
      periodEvents,
      reservationEvents,
      monthDays,
      weekDays,
      selectedDay,
      monthReservationCount: countReservationsForDays(events, monthDays),
      weekReservationCount: countReservationsForDays(events, weekDays),
      selectedDayReservationCount: countReservationsForDays(events, selectedDay),
      stayCounts,
      maxStayCount,
      dailyCounts,
      maxDailyCount,
      topGuests,
      mostBooked,
      hasMostBooked: Boolean(mostBooked?.count),
      recordMix: {
        reservations: reservationEvents.length,
        blocks: periodEvents.filter((event) => event.type === 'block').length,
        prices: periodEvents.filter((event) => event.type === 'price').length,
      },
    };
  }

  analyticsForPeriod(view: OpsCalendarViewMode, focusDate: string, showWeekends = true, filters: CalendarWorkspaceFilters = {}): CalendarPeriodAnalytics {
    const rows = this.visibleRows(filters);
    const days = fallbackVisibleDays(rows, view, focusDate, this.periodDays(view, focusDate, showWeekends, rows[0]?.row));
    const dates = days.map((day) => day.date);
    const events = this.filteredEvents(filters).filter((event) => eventOverlapsDates(event, dates));
    return {
      days,
      dates,
      events,
      reservations: events.filter((event) => event.type === 'reservation'),
      blocks: events.filter((event) => event.type === 'block'),
      priceOverrides: events.filter((event) => event.type === 'price'),
    };
  }
}
