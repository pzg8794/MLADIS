import { CSSProperties, FormEvent, MouseEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  BarChart3,
  Bell,
  Building2,
  CalendarDays,
  CheckCircle2,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Clock3,
  DollarSign,
  ExternalLink,
  Filter,
  Home,
  LayoutList,
  LockKeyhole,
  Moon,
  MapPin,
  Monitor,
  Palette,
  Plus,
  Search,
  Settings,
  Shield,
  Sparkles,
  Square,
  Sun,
  Trash2,
  User,
  Users,
  X,
  type LucideIcon,
} from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import {
  OpsCalendarDay,
  OpsCalendarEvent,
  OpsCalendarSnapshot,
  OpsCalendarStayRow,
  OpsCalendarViewMode,
} from '../../domain/models';
import { CalendarAnalyticsView, CalendarListView, CalendarRoomsView } from './calendar/CalendarWorkspaceViews';

type RangeState = {
  start: string;
  end: string;
};

type BlockFormState = {
  reason: string;
  notes: string;
};

type GridCellPosition = {
  rowIndex: number;
  colIndex: number;
};

type StayRowWithMeta = {
  row: OpsCalendarStayRow;
  meta: StayVisualMeta;
};

type StayVisualMeta = {
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

type DayModalState = {
  day: OpsCalendarDay;
  row: StayRowWithMeta;
};

type SelectionModalState = {
  rows: StayRowWithMeta[];
  dates: OpsCalendarDay[];
};

type BookingDraftFormState = {
  title: string;
  startTime: string;
  endTime: string;
  bookedBy: string;
  notes: string;
};

type CalendarWorkspaceSection = 'calendar' | 'list' | 'rooms' | 'analytics';
type StayFilterId = 'all' | number;
type CalendarSettingsSection = 'profile' | 'notifications' | 'appearance' | 'booking' | 'rooms' | 'security';

const viewModes: OpsCalendarViewMode[] = ['month', 'week', 'list'];
const viewLabels: Record<OpsCalendarViewMode, string> = {
  month: 'Month',
  week: 'Week',
  list: 'Day',
};

const roomPalette = [
  { color: '#6750a4', bgColor: '#eaddff', textColor: '#21005d' },
  { color: '#0072b8', bgColor: '#d5ebff', textColor: '#003257' },
  { color: '#c25100', bgColor: '#ffdac6', textColor: '#4b1900' },
  { color: '#087927', bgColor: '#c7f3d1', textColor: '#00390f' },
  { color: '#7d5260', bgColor: '#ffd8e4', textColor: '#31111d' },
  { color: '#546524', bgColor: '#dceac0', textColor: '#202900' },
];

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

const calendarSettingsSections: {
  id: CalendarSettingsSection;
  label: string;
  desc: string;
  icon: LucideIcon;
}[] = [
  { id: 'profile', label: 'Profile', desc: 'Operator identity', icon: User },
  { id: 'notifications', label: 'Notifications', desc: 'Alerts and reminders', icon: Bell },
  { id: 'appearance', label: 'Appearance', desc: 'Theme and density', icon: Palette },
  { id: 'booking', label: 'Booking rules', desc: 'Defaults and limits', icon: Clock3 },
  { id: 'rooms', label: 'Stays', desc: 'Calendar resources', icon: Building2 },
  { id: 'security', label: 'Security', desc: 'Access and sessions', icon: Shield },
];

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function dateFromIso(value: string) {
  return new Date(`${value}T00:00:00`);
}

function compactDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dateFromIso(value));
}

function longDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).format(dateFromIso(value));
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

function isoMonth(value: string) {
  return value.slice(0, 7);
}

function sortedRange(first: string, second: string): RangeState {
  return first <= second ? { start: first, end: second } : { start: second, end: first };
}

function eventCoversDay(event: OpsCalendarEvent, date: string) {
  if (event.type === 'reservation') {
    return event.start <= date && date < event.end;
  }
  return event.start <= date && date <= event.end;
}

function eventTone(event: OpsCalendarEvent) {
  if (event.type === 'reservation') return 'booking';
  if (event.type === 'block') return 'block';
  return 'price';
}

function eventLabel(event: OpsCalendarEvent) {
  if (event.type === 'reservation') return event.guestLabel || 'Reservation';
  if (event.type === 'block') return 'Blocked';
  return event.amount || 'Price';
}

function rangeLabel(range: RangeState) {
  if (!range.start) return 'Select dates on the calendar';
  if (!range.end || range.start === range.end) return longDate(range.start);
  return `${compactDate(range.start)} - ${compactDate(range.end)}`;
}

function dateRangeLabel(days: OpsCalendarDay[]) {
  if (days.length === 0) return '';
  if (days.length === 1) return fullDate(days[0].date);
  return `${compactDate(days[0].date)} - ${compactDate(days[days.length - 1].date)}, ${dateFromIso(days[days.length - 1].date).getFullYear()} (${days.length} days)`;
}

function getRowDays(row: OpsCalendarStayRow, mode: OpsCalendarViewMode, focusDate: string) {
  if (mode === 'month') return row.weeks.flat();
  if (mode === 'week') return row.weekDays;
  const allDays = row.weeks.flat();
  return allDays.filter((day) => day.date === focusDate);
}

function isWeekendIso(value: string) {
  const day = dateFromIso(value).getDay();
  return day === 0 || day === 6;
}

function daysForWeekendPreference(days: OpsCalendarDay[], showWeekends: boolean) {
  return showWeekends ? days : days.filter((day) => !isWeekendIso(day.date));
}

function selectedGridCoversCell(start: GridCellPosition | null, end: GridCellPosition | null, rowIndex: number, colIndex: number) {
  if (!start || !end) return false;
  const rowStart = Math.min(start.rowIndex, end.rowIndex);
  const rowEnd = Math.max(start.rowIndex, end.rowIndex);
  const colStart = Math.min(start.colIndex, end.colIndex);
  const colEnd = Math.max(start.colIndex, end.colIndex);
  return rowIndex >= rowStart && rowIndex <= rowEnd && colIndex >= colStart && colIndex <= colEnd;
}

function selectionFromCells(rows: StayRowWithMeta[], mode: OpsCalendarViewMode, focusDate: string, showWeekends: boolean, start: GridCellPosition, end: GridCellPosition): SelectionModalState {
  const rowStart = Math.min(start.rowIndex, end.rowIndex);
  const rowEnd = Math.max(start.rowIndex, end.rowIndex);
  const colStart = Math.min(start.colIndex, end.colIndex);
  const colEnd = Math.max(start.colIndex, end.colIndex);
  const selectedRows = rows.slice(rowStart, rowEnd + 1);
  const firstRow = rows[0]?.row;
  const days = firstRow ? daysForWeekendPreference(getRowDays(firstRow, mode, focusDate), showWeekends).slice(colStart, colEnd + 1) : [];
  return { rows: selectedRows, dates: days };
}

function emptyRange(focusDate: string): RangeState {
  return { start: focusDate, end: focusDate };
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

function visualMetaForRow(row: OpsCalendarStayRow, index: number): StayVisualMeta {
  const tone = roomPalette[index % roomPalette.length];
  const identity = lockedStayIdentity(row.stay.name, row.stay.subtitle, index);
  return {
    ...tone,
    index,
    ...identity,
  };
}

export function OpsCalendarPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const currentSection = useMemo<CalendarWorkspaceSection>(() => {
    const path = window.location.pathname;
    if (path.includes('/ops/calendar/list')) return 'list';
    if (path.includes('/ops/calendar/rooms')) return 'rooms';
    if (path.includes('/ops/calendar/analytics')) return 'analytics';
    return 'calendar';
  }, []);
  const [snapshot, setSnapshot] = useState<OpsCalendarSnapshot | null>(null);
  const [error, setError] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const [selectedItemId, setSelectedItemId] = useState<number | null>(() => {
    const item = params.get('item');
    return item ? Number(item) : null;
  });
  const [activeStayFilter, setActiveStayFilter] = useState<number | 'all'>(() => {
    const item = params.get('item');
    return item ? Number(item) : 'all';
  });
  const [activeStayFilters, setActiveStayFilters] = useState<Set<StayFilterId>>(() => {
    const item = params.get('item');
    return item ? new Set<StayFilterId>([Number(item)]) : new Set<StayFilterId>(['all']);
  });
  const [view, setView] = useState<OpsCalendarViewMode>(() => {
    const value = params.get('view') as OpsCalendarViewMode | null;
    return value && viewModes.includes(value) ? value : 'month';
  });
  const [focusDate, setFocusDate] = useState(params.get('date') || todayIso());
  const [search, setSearch] = useState('');
  const [toolbarSearchOpen, setToolbarSearchOpen] = useState(false);
  const [filterPanelOpen, setFilterPanelOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(() => params.get('panel') === 'settings');
  const [showWeekends, setShowWeekends] = useState(true);
  const [railExpanded, setRailExpanded] = useState(false);
  const [selectedRange, setSelectedRange] = useState<RangeState>(() => emptyRange(params.get('date') || todayIso()));
  const [blockForm] = useState<BlockFormState>({ reason: 'Direct booking hold', notes: '' });
  const [dragStart, setDragStart] = useState<GridCellPosition | null>(null);
  const [dragEnd, setDragEnd] = useState<GridCellPosition | null>(null);
  const [dayModal, setDayModal] = useState<DayModalState | null>(null);
  const [selectionModal, setSelectionModal] = useState<SelectionModalState | null>(null);
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef<GridCellPosition | null>(null);
  const dragEndRef = useRef<GridCellPosition | null>(null);
  const visibleRowsRef = useRef<StayRowWithMeta[]>([]);
  const viewRef = useRef<OpsCalendarViewMode>(view);
  const focusDateRef = useRef(focusDate);
  const showWeekendsRef = useRef(showWeekends);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const filterRef = useRef<HTMLDivElement | null>(null);

  const loadSnapshot = useCallback(() => {
    service
      .loadCalendar({ itemId: null, view, date: focusDate })
      .then((data) => {
        setSnapshot(data);
        setError('');
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : 'Could not load calendar.');
      });
  }, [focusDate, service, view]);

  useEffect(() => {
    loadSnapshot();
  }, [loadSnapshot]);

  const rowsWithMeta = useMemo<StayRowWithMeta[]>(() => (
    snapshot?.stayRows
      .map((row, index) => ({ row, meta: visualMetaForRow(row, index) }))
      .filter(({ meta }) => !meta.isDemo) || []
  ), [snapshot]);

  const visibleRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    return rowsWithMeta.filter(({ row, meta }) => {
      const matchesActiveFilter = activeStayFilters.has('all') || activeStayFilters.has(row.stay.id);
      if (!matchesActiveFilter) return false;
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
    });
  }, [activeStayFilters, rowsWithMeta, search]);

  useEffect(() => {
    visibleRowsRef.current = visibleRows;
    viewRef.current = view;
    focusDateRef.current = focusDate;
    showWeekendsRef.current = showWeekends;
  }, [focusDate, showWeekends, view, visibleRows]);

  const selectedStay = useMemo(() => {
    if (!snapshot) return null;
    const id = activeStayFilter === 'all' ? selectedItemId : activeStayFilter;
    return rowsWithMeta.find(({ row }) => row.stay.id === id) || rowsWithMeta[0] || null;
  }, [activeStayFilter, rowsWithMeta, selectedItemId, snapshot]);

  const filteredEvents = useMemo(() => {
    const events = rowsWithMeta.flatMap(({ row }) => row.events);
    const seen = new Map<string, OpsCalendarEvent>();
    events.forEach((event) => seen.set(event.id, event));
    const query = search.trim().toLowerCase();
    return Array.from(seen.values()).filter((event) => {
      const inFilter = activeStayFilters.has('all') || activeStayFilters.has(event.itemId);
      if (!inFilter) return false;
      if (!query) return true;
      return [
        event.title,
        event.subtitle,
        event.itemName,
        event.guestLabel,
        event.rangeLabel,
        rowsWithMeta.find(({ row }) => row.stay.id === event.itemId)?.meta.displayName || '',
        rowsWithMeta.find(({ row }) => row.stay.id === event.itemId)?.meta.shortLabel || '',
      ].some((value) => value.toLowerCase().includes(query));
    });
  }, [activeStayFilters, rowsWithMeta, search]);

  const reservationCount = useMemo(() => (
    filteredEvents.filter((event) => event.type === 'reservation').length
  ), [filteredEvents]);

  const visibleDays = visibleRows[0] ? daysForWeekendPreference(getRowDays(visibleRows[0].row, view, focusDate), showWeekends) : [];
  const selectedVisualRows = selectionModal?.rows || [];
  const selectedVisualDates = selectionModal?.dates || [];
  const hiddenFilterCount = activeStayFilters.has('all') ? 0 : Math.max(rowsWithMeta.length - activeStayFilters.size, 0);
  const selectedFilterSummary = activeStayFilters.has('all')
    ? 'Showing all stays'
    : `${activeStayFilters.size} stay${activeStayFilters.size === 1 ? '' : 's'} selected`;

  function chooseFilter(nextFilter: number | 'all') {
    setActiveStayFilter(nextFilter);
    setSelectedItemId(nextFilter === 'all' ? null : nextFilter);
    setActiveStayFilters(nextFilter === 'all' ? new Set<StayFilterId>(['all']) : new Set<StayFilterId>([nextFilter]));
  }

  function toggleStayFilter(nextFilter: StayFilterId) {
    if (nextFilter === 'all') {
      chooseFilter('all');
      return;
    }

    setActiveStayFilters((current) => {
      const next = new Set<StayFilterId>(current);
      if (next.has('all')) {
        next.clear();
        next.add(nextFilter);
      } else if (next.has(nextFilter)) {
        next.delete(nextFilter);
      } else {
        next.add(nextFilter);
      }

      if (next.size === 0 || next.size >= rowsWithMeta.length) {
        setActiveStayFilter('all');
        setSelectedItemId(null);
        return new Set<StayFilterId>(['all']);
      }

      const first = Array.from(next)[0];
      setActiveStayFilter(next.size === 1 && typeof first === 'number' ? first : 'all');
      setSelectedItemId(next.size === 1 && typeof first === 'number' ? first : null);
      return next;
    });
  }

  function resetFilters() {
    setSearch('');
    chooseFilter('all');
    setShowWeekends(true);
  }

  function showToolbarSearch() {
    setToolbarSearchOpen(true);
    window.setTimeout(() => searchInputRef.current?.focus(), 0);
  }

  function closeToolbarSearch() {
    setSearch('');
    setToolbarSearchOpen(false);
  }

  function selectPeriod(date: string, mode: OpsCalendarViewMode = view) {
    setFocusDate(date);
    setView(mode);
    setSelectedRange(emptyRange(date));
  }

  function beginCellDrag(event: MouseEvent<HTMLButtonElement>, rowIndex: number, colIndex: number) {
    event.preventDefault();
    const position = { rowIndex, colIndex };
    isDraggingRef.current = true;
    dragStartRef.current = position;
    dragEndRef.current = position;
    setDragStart(position);
    setDragEnd(position);
  }

  function enterCell(rowIndex: number, colIndex: number) {
    if (!isDraggingRef.current) return;
    const position = { rowIndex, colIndex };
    dragEndRef.current = position;
    setDragEnd(position);
  }

  useEffect(() => {
    function finishDrag() {
      if (!isDraggingRef.current) return;
      isDraggingRef.current = false;
      const start = dragStartRef.current;
      const end = dragEndRef.current;
      if (!start || !end) return;

      const rows = visibleRowsRef.current;
      const selection = selectionFromCells(rows, viewRef.current, focusDateRef.current, showWeekendsRef.current, start, end);
      const sameCell = start.rowIndex === end.rowIndex && start.colIndex === end.colIndex;
      if (sameCell) {
        const row = selection.rows[0];
        const day = selection.dates[0];
        if (row && day) {
          setSelectedItemId(row.row.stay.id);
          setActiveStayFilter((current) => current === 'all' ? 'all' : row.row.stay.id);
          setSelectedRange({ start: day.date, end: day.date });
          setDayModal({ row, day });
        }
        setDragStart(null);
        setDragEnd(null);
        return;
      }

      if (selection.rows.length > 0 && selection.dates.length > 0) {
        const first = selection.dates[0].date;
        const last = selection.dates[selection.dates.length - 1].date;
        setSelectedItemId(selection.rows[0].row.stay.id);
        setSelectedRange(sortedRange(first, last));
        setSelectionModal(selection);
      }
    }

    window.addEventListener('mouseup', finishDrag);
    return () => window.removeEventListener('mouseup', finishDrag);
  }, []);

  useEffect(() => {
    if (!filterPanelOpen) return undefined;
    function closeOnOutsideClick(event: globalThis.MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(event.target as Node)) {
        setFilterPanelOpen(false);
      }
    }
    document.addEventListener('mousedown', closeOnOutsideClick);
    return () => document.removeEventListener('mousedown', closeOnOutsideClick);
  }, [filterPanelOpen]);

  useEffect(() => {
    document.body.classList.toggle('calendar-is-dragging', isDraggingRef.current);
    return () => document.body.classList.remove('calendar-is-dragging');
  }, [dragStart, dragEnd]);

  async function createBookingHold(data: BookingDraftFormState, selection: SelectionModalState) {
    if (selection.rows.length === 0 || selection.dates.length === 0) return;
    const firstDate = selection.dates[0].date;
    const lastDate = selection.dates[selection.dates.length - 1].date;
    setActionMessage('Creating booking hold...');
    await Promise.all(selection.rows.map(({ row }) => service.createCalendarBlock({
      item: row.stay.id,
      start_date: firstDate,
      end_date: lastDate,
      reason: data.title || blockForm.reason,
      notes: [
        data.bookedBy ? `Booked by: ${data.bookedBy}` : '',
        `${data.startTime} - ${data.endTime}`,
        data.notes,
      ].filter(Boolean).join('\n'),
    })));
    setSelectionModal(null);
    setDragStart(null);
    setDragEnd(null);
    setActionMessage('Booking hold created.');
    loadSnapshot();
    window.setTimeout(() => setActionMessage(''), 2400);
  }

  async function deleteEvent(event: OpsCalendarEvent) {
    setActionMessage(`Removing ${event.title}...`);
    if (event.type === 'block') {
      await service.deleteCalendarBlock(event.recordId);
    } else if (event.type === 'price') {
      await service.deleteCalendarPrice(event.recordId);
    }
    setActionMessage('Calendar record removed.');
    loadSnapshot();
    window.setTimeout(() => setActionMessage(''), 2400);
  }

  function openQuickBooking() {
    const targetRow = selectedStay || visibleRows[0];
    const targetDay = visibleDays.find((day) => day.date === focusDate)
      || visibleDays.find((day) => day.isToday)
      || visibleDays[0];
    if (!targetRow || !targetDay) {
      setActionMessage('Select a stay and date before creating a booking.');
      window.setTimeout(() => setActionMessage(''), 2400);
      return;
    }
    setSelectionModal({ rows: [targetRow], dates: [targetDay] });
  }

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="calendar-product-shell"><section className="calendar-product-loading" /></main>;
  }

  return (
    <main className={`calendar-product-shell ${railExpanded ? 'is-rail-expanded' : 'is-rail-compact'}`}>
      <aside
        className="calendar-product-rail"
        onMouseEnter={() => setRailExpanded(true)}
        onMouseLeave={() => setRailExpanded(false)}
      >
        <a className="calendar-product-brand" href="/">
          <span><CalendarDays size={26} /></span>
          <strong>Booking Calendar</strong>
        </a>

        <nav className="calendar-product-nav" aria-label="Calendar workspace">
          <a className={currentSection === 'calendar' ? 'is-active' : ''} href="/ops/calendar/"><CalendarDays size={26} /><span>Calendar</span></a>
          <a className={currentSection === 'list' ? 'is-active' : ''} href="/ops/calendar/list/"><LayoutList size={26} /><span>List View</span></a>
          <a className={currentSection === 'rooms' ? 'is-active' : ''} href="/ops/calendar/rooms/"><Building2 size={26} /><span>Rooms</span></a>
          <a className={currentSection === 'analytics' ? 'is-active' : ''} href="/ops/calendar/analytics/"><BarChart3 size={26} /><span>Analytics</span></a>
        </nav>

        <div className="calendar-product-rail__bottom">
          <button
            type="button"
            className={settingsOpen ? 'is-active' : ''}
            aria-label="Calendar settings"
            aria-expanded={settingsOpen}
            onClick={() => {
              setSettingsOpen((current) => !current);
              setNotificationsOpen(false);
            }}
          >
            <Settings size={26} /><span>Settings</span>
          </button>
          <button type="button" className="calendar-product-new-booking" onClick={openQuickBooking}>
            <Plus size={26} /><span>New Booking</span>
          </button>
        </div>
      </aside>

      <section className="calendar-product-main">
        <header className="calendar-product-header">
          <div className="calendar-product-title">
            <h1>Booking Calendar</h1>
            <p>{snapshot.monthLabel} · {reservationCount} bookings this month</p>
          </div>

          <div className="calendar-product-room-stats" aria-label="Stay booking totals">
            {rowsWithMeta.slice(0, 5).map(({ row, meta }) => {
              const count = row.events.filter((event) => event.type === 'reservation').length;
              return (
                <button
                  className={activeStayFilter === row.stay.id ? 'is-active' : ''}
                  key={row.stay.id}
                  type="button"
                  onClick={() => chooseFilter(row.stay.id)}
                  style={{ '--room-color': meta.color, '--room-bg': meta.bgColor } as CSSProperties}
                >
                  <span /> {meta.unitLabel} · {count}
                </button>
              );
            })}
          </div>

          <div className="calendar-product-header__actions">
            <button type="button" aria-label="Previous period" onClick={() => selectPeriod(snapshot.previousDate)}><ChevronLeft /></button>
            <button className="calendar-product-today" type="button" onClick={() => selectPeriod(todayIso())}>Today</button>
            <button type="button" aria-label="Next period" onClick={() => selectPeriod(snapshot.nextDate)}><ChevronRight /></button>
            <div className={`calendar-product-header-search ${toolbarSearchOpen || search ? 'is-open' : ''}`}>
              {toolbarSearchOpen || search ? (
                <label>
                  <Search size={17} />
                  <input
                    ref={searchInputRef}
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Escape') closeToolbarSearch();
                    }}
                    placeholder="Search stays or bookings..."
                  />
                  <button type="button" aria-label="Clear calendar search" onClick={closeToolbarSearch}><X size={16} /></button>
                </label>
              ) : (
                <button type="button" aria-label="Search calendar" onClick={showToolbarSearch}><Search /></button>
              )}
            </div>
            <button
              className={notificationsOpen ? 'is-active' : ''}
              type="button"
              aria-label="Calendar notifications"
              aria-expanded={notificationsOpen}
              onClick={() => {
                setNotificationsOpen((current) => !current);
                setSettingsOpen(false);
              }}
            >
              <Bell />
            </button>
          </div>
        </header>

        <div className={`calendar-product-toolbar ${currentSection === 'calendar' ? '' : 'calendar-product-toolbar--subview'}`}>
          <div className="calendar-product-view-switch" aria-label="Calendar views">
            {viewModes.map((mode) => (
              <button
                className={view === mode ? 'is-active' : ''}
                key={mode}
                type="button"
                onClick={() => {
                  setView(mode);
                  setSelectedRange(emptyRange(focusDate));
                  setDayModal(null);
                  setSelectionModal(null);
                }}
              >
                {viewLabels[mode]}
              </button>
            ))}
          </div>

          <div className="calendar-product-filter-chips">
            <button className={activeStayFilter === 'all' ? 'is-active' : ''} type="button" onClick={() => chooseFilter('all')}>
              <Home size={16} /> All
            </button>
            {rowsWithMeta.map(({ row, meta }) => (
              <button
                className={activeStayFilters.has('all') || activeStayFilters.has(row.stay.id) ? 'is-active' : ''}
                key={row.stay.id}
                type="button"
                onClick={() => toggleStayFilter(row.stay.id)}
                style={{ '--room-color': meta.color, '--room-bg': meta.bgColor } as CSSProperties}
              >
                <span /> {meta.unitLabel}
              </button>
            ))}
          </div>

          <span className="calendar-product-hint">
            {search ? `Search: ${search}` : 'Click a cell to view · Drag to multi-book'}
          </span>

          <div className="calendar-product-filter-wrap" ref={filterRef}>
            <button
              className={`calendar-product-filter-button ${filterPanelOpen ? 'is-active' : ''}`}
              type="button"
              aria-expanded={filterPanelOpen}
              onClick={() => setFilterPanelOpen((current) => !current)}
            >
              <Filter size={19} />
              Filter
              {hiddenFilterCount > 0 && <span className="calendar-product-filter-badge">{hiddenFilterCount}</span>}
            </button>

            {filterPanelOpen && (
              <section className="calendar-product-filter-panel" aria-label="Calendar filters">
                <header>
                  <strong>Filter Stays</strong>
                  <button type="button" onClick={resetFilters}>Reset</button>
                </header>

                <div className="calendar-product-filter-panel__rows">
                  <button
                    className={activeStayFilters.has('all') ? 'is-active' : ''}
                    type="button"
                    onClick={() => chooseFilter('all')}
                  >
                    {activeStayFilters.has('all') ? <CheckSquare size={18} /> : <Square size={18} />}
                    <span className="calendar-product-filter-dot is-neutral" />
                    <b>All</b>
                    <em>{rowsWithMeta.length} stays</em>
                  </button>
                  {rowsWithMeta.map(({ row, meta }) => {
                    const checked = activeStayFilters.has('all') || activeStayFilters.has(row.stay.id);
                    return (
                      <button
                        className={checked ? 'is-active' : ''}
                        key={row.stay.id}
                        type="button"
                        onClick={() => toggleStayFilter(row.stay.id)}
                        style={{ '--room-color': meta.color, '--room-bg': meta.bgColor } as CSSProperties}
                      >
                        {checked ? <CheckSquare size={18} /> : <Square size={18} />}
                        <span className="calendar-product-filter-dot" />
                        <b>{meta.unitLabel}</b>
                        <em>{meta.capacityLabel}</em>
                      </button>
                    );
                  })}
                </div>

                <footer>
                  <p>Show Weekends</p>
                  <div>
                    <button className={showWeekends ? 'is-active' : ''} type="button" onClick={() => setShowWeekends(true)}>Yes</button>
                    <button className={!showWeekends ? 'is-active' : ''} type="button" onClick={() => setShowWeekends(false)}>No</button>
                  </div>
                  <small>{selectedFilterSummary}</small>
                </footer>
              </section>
            )}
          </div>
        </div>

        {currentSection === 'calendar' && (
          <>
            <CalendarMatrix
              dragEnd={dragEnd}
              dragStart={dragStart}
              mode={view}
              rows={visibleRows}
              search={search}
              showWeekends={showWeekends}
              focusDate={focusDate}
              visibleDays={visibleDays}
              onCellEnter={enterCell}
              onCellMouseDown={beginCellDrag}
            />

            <section className="calendar-product-footer">
              <article>
                <strong>{activeStayFilter === 'all' ? 'All' : selectedStay?.meta.displayName || 'All'}</strong>
                <span>{rangeLabel(selectedRange)}</span>
              </article>
              <div className="calendar-product-legend" aria-label="Calendar legend">
                <span><i className="is-available" /> Available</span>
                <span><i className="is-booked" /> Reservation</span>
                <span><i className="is-blocked" /> Blocked</span>
                <span><i className="is-priced" /> Price override</span>
              </div>
            </section>
          </>
        )}

        {currentSection === 'list' && <CalendarListView focusDate={focusDate} globalSearch={search} rows={visibleRows} view={view} visibleDays={visibleDays} />}
        {currentSection === 'rooms' && <CalendarRoomsView focusDate={focusDate} globalSearch={search} rows={visibleRows} view={view} visibleDays={visibleDays} />}
        {currentSection === 'analytics' && <CalendarAnalyticsView focusDate={focusDate} globalSearch={search} rows={visibleRows} view={view} visibleDays={visibleDays} />}
      </section>

      {dayModal && (
        <CalendarDayDetailsModal
          activeDay={dayModal.day}
          initialRow={dayModal.row}
          rows={rowsWithMeta}
          onClose={() => setDayModal(null)}
        />
      )}

      {selectionModal && (
        <CalendarSelectionModal
          selectedDates={selectedVisualDates}
          selectedRows={selectedVisualRows}
          onClose={() => {
            setSelectionModal(null);
            setDragStart(null);
            setDragEnd(null);
          }}
          onConfirm={(formData) => createBookingHold(formData, selectionModal)}
        />
      )}

      <CalendarNotificationsPanel
        isOpen={notificationsOpen}
        rows={rowsWithMeta}
        events={filteredEvents}
        onClose={() => setNotificationsOpen(false)}
      />

      <CalendarSettingsPanel
        isOpen={settingsOpen}
        rows={rowsWithMeta}
        view={view}
        showWeekends={showWeekends}
        selectedFilterSummary={selectedFilterSummary}
        onClose={() => setSettingsOpen(false)}
        onShowWeekendsChange={setShowWeekends}
      />

      {actionMessage && (
        <div className="ops-calendar-toast">
          <CheckCircle2 size={16} /> {actionMessage}
        </div>
      )}
    </main>
  );
}

function CalendarNotificationsPanel({
  isOpen,
  rows,
  events,
  onClose,
}: {
  isOpen: boolean;
  rows: StayRowWithMeta[];
  events: OpsCalendarEvent[];
  onClose: () => void;
}) {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const feedWarnings = rows
    .filter(({ row }) => !row.stay.isConfigured)
    .map(({ row, meta }) => ({
      id: `feed-${row.stay.id}`,
      type: 'alert' as const,
      title: 'Airbnb feed needs setup',
      body: `${meta.displayName} does not have an active iCal feed yet.`,
      date: '',
      color: meta.color,
    }));
  const eventNotifications = events
    .filter((event) => event.type === 'reservation' || event.type === 'block')
    .slice(0, 8)
    .map((event) => {
      const meta = rows.find(({ row }) => row.stay.id === event.itemId)?.meta;
      return {
        id: event.id,
        type: event.type === 'reservation' ? 'booking' as const : 'alert' as const,
        title: event.type === 'reservation' ? 'Reservation on calendar' : 'Blocked dates',
        body: `${meta?.displayName || event.itemName}: ${eventLabel(event)}`,
        date: event.rangeLabel,
        color: meta?.color || '#6750a4',
      };
    });
  const notifications = [...feedWarnings, ...eventNotifications].filter((item) => !dismissed.has(item.id));
  const unread = notifications.length;

  if (!isOpen) return null;

  return (
    <div className="calendar-drawer-backdrop" role="presentation" onClick={onClose}>
      <aside className="calendar-side-panel" role="dialog" aria-modal="true" aria-label="Calendar notifications" onClick={(event) => event.stopPropagation()}>
        <header>
          <div>
            <span><Bell size={17} /> Notifications</span>
            <h3>{unread} active alert{unread === 1 ? '' : 's'}</h3>
          </div>
          <button type="button" aria-label="Close notifications" onClick={onClose}><X size={18} /></button>
        </header>
        <div className="calendar-side-panel__body">
          {notifications.length === 0 ? (
            <article className="calendar-side-empty">
              <CheckCircle2 size={28} />
              <strong>All clear</strong>
              <p>No active calendar notifications for the current view.</p>
            </article>
          ) : (
            notifications.map((item) => (
              <article className={`calendar-notification calendar-notification--${item.type}`} key={item.id} style={{ '--room-color': item.color } as CSSProperties}>
                <i />
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.body}</p>
                  {item.date && <small>{item.date}</small>}
                </div>
                <button type="button" aria-label={`Dismiss ${item.title}`} onClick={() => setDismissed((current) => new Set([...current, item.id]))}>
                  <X size={14} />
                </button>
              </article>
            ))
          )}
        </div>
      </aside>
    </div>
  );
}

function CalendarSettingsPanel({
  isOpen,
  rows,
  view,
  showWeekends,
  selectedFilterSummary,
  onClose,
  onShowWeekendsChange,
}: {
  isOpen: boolean;
  rows: StayRowWithMeta[];
  view: OpsCalendarViewMode;
  showWeekends: boolean;
  selectedFilterSummary: string;
  onClose: () => void;
  onShowWeekendsChange: (value: boolean) => void;
}) {
  const [activeSection, setActiveSection] = useState<CalendarSettingsSection>('profile');
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [bookingReminders, setBookingReminders] = useState(true);
  const [dailyDigest, setDailyDigest] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [compactView, setCompactView] = useState(false);
  const [showCapacity, setShowCapacity] = useState(true);
  const [showAmenities, setShowAmenities] = useState(true);
  const [autoRelease, setAutoRelease] = useState(false);
  const [twoFactor, setTwoFactor] = useState(false);

  if (!isOpen) return null;
  const configured = rows.filter(({ row }) => row.stay.isConfigured).length;
  const active = calendarSettingsSections.find((section) => section.id === activeSection) || calendarSettingsSections[0];

  return (
    <div className="calendar-drawer-backdrop" role="presentation" onClick={onClose}>
      <aside className="calendar-settings-panel" role="dialog" aria-modal="true" aria-label="Calendar settings" onClick={(event) => event.stopPropagation()}>
        <header className="calendar-settings-panel__header">
          <div>
            <span><Settings size={17} /> Calendar settings</span>
            <h3>Room booking controls</h3>
          </div>
          <button type="button" aria-label="Close settings" onClick={onClose}><X size={18} /></button>
        </header>

        <div className="calendar-settings-panel__layout">
          <nav className="calendar-settings-panel__sections" aria-label="Calendar settings sections">
            {calendarSettingsSections.map((section) => {
              const Icon = section.icon;
              return (
                <button
                  className={activeSection === section.id ? 'is-active' : ''}
                  key={section.id}
                  type="button"
                  onClick={() => setActiveSection(section.id)}
                >
                  <Icon size={17} />
                  <span>{section.label}</span>
                  <small>{section.desc}</small>
                </button>
              );
            })}
          </nav>

          <section className="calendar-settings-panel__content">
            <h4>{active.label}</h4>

            {activeSection === 'profile' && (
              <div className="calendar-settings-stack">
                <div className="calendar-settings-profile">
                  <span>JD</span>
                  <div>
                    <strong>MLADIS calendar admin</strong>
                    <p>Staff workspace for availability, holds, stay sync, and reservation review.</p>
                  </div>
                </div>
                <label className="calendar-settings-field">
                  <span>Display name</span>
                  <input defaultValue="MLADIS Operations" />
                </label>
                <label className="calendar-settings-field">
                  <span>Calendar email</span>
                  <input defaultValue="agent-admin@mladis.com" type="email" />
                </label>
                <label className="calendar-settings-field">
                  <span>Role</span>
                  <select defaultValue="admin">
                    <option value="admin">Admin</option>
                    <option value="manager">Manager</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </label>
              </div>
            )}

            {activeSection === 'notifications' && (
              <div className="calendar-settings-stack">
                <CalendarSettingRow label="Email notifications" desc="Reservation holds, feed failures, and admin reminders.">
                  <CalendarSettingsToggle value={emailNotifications} onChange={setEmailNotifications} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Push notifications" desc="In-app alerts for new booking activity.">
                  <CalendarSettingsToggle value={pushNotifications} onChange={setPushNotifications} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Booking reminders" desc="Remind admins before check-in and checkout windows.">
                  <CalendarSettingsToggle value={bookingReminders} onChange={setBookingReminders} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Daily digest" desc="Morning summary of stays, holds, and feed issues.">
                  <CalendarSettingsToggle value={dailyDigest} onChange={setDailyDigest} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Reminder lead time" desc="How early a stay reminder should appear.">
                  <select className="calendar-settings-select" defaultValue="24">
                    <option value="2">2 hours</option>
                    <option value="12">12 hours</option>
                    <option value="24">24 hours</option>
                    <option value="48">48 hours</option>
                  </select>
                </CalendarSettingRow>
              </div>
            )}

            {activeSection === 'appearance' && (
              <div className="calendar-settings-stack">
                <div className="calendar-settings-theme-grid" aria-label="Calendar theme">
                  {[
                    { id: 'light', label: 'Light', icon: Sun },
                    { id: 'dark', label: 'Dark', icon: Moon },
                    { id: 'system', label: 'System', icon: Monitor },
                  ].map((option) => {
                    const Icon = option.icon;
                    return (
                      <button
                        className={theme === option.id ? 'is-active' : ''}
                        key={option.id}
                        type="button"
                        onClick={() => setTheme(option.id as 'light' | 'dark' | 'system')}
                      >
                        <Icon size={18} />
                        <span>{option.label}</span>
                      </button>
                    );
                  })}
                </div>
                <CalendarSettingRow label="Compact view" desc="Reduce row height to fit more stay rows.">
                  <CalendarSettingsToggle value={compactView} onChange={setCompactView} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Show weekends" desc="Include Saturday and Sunday in the grid.">
                  <CalendarSettingsToggle value={showWeekends} onChange={onShowWeekendsChange} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Current view" desc={`${viewLabels[view]} view. ${selectedFilterSummary}.`}>
                  <span className="calendar-settings-pill">{viewLabels[view]}</span>
                </CalendarSettingRow>
              </div>
            )}

            {activeSection === 'booking' && (
              <div className="calendar-settings-stack">
                <CalendarSettingRow label="Default check-in" desc="Used when quick booking creates a hold.">
                  <select className="calendar-settings-select" defaultValue="15:00">
                    <option value="14:00">2:00 PM</option>
                    <option value="15:00">3:00 PM</option>
                    <option value="16:00">4:00 PM</option>
                  </select>
                </CalendarSettingRow>
                <CalendarSettingRow label="Default checkout" desc="Used when quick booking creates a hold.">
                  <select className="calendar-settings-select" defaultValue="12:00">
                    <option value="11:00">11:00 AM</option>
                    <option value="12:00">12:00 PM</option>
                    <option value="13:00">1:00 PM</option>
                  </select>
                </CalendarSettingRow>
                <CalendarSettingRow label="Buffer between stays" desc="Optional cleanup/readiness gap.">
                  <select className="calendar-settings-select" defaultValue="0">
                    <option value="0">None</option>
                    <option value="1">1 day</option>
                    <option value="2">2 days</option>
                  </select>
                </CalendarSettingRow>
                <CalendarSettingRow label="Auto-release tentative holds" desc="Release unpaid direct holds after review window.">
                  <CalendarSettingsToggle value={autoRelease} onChange={setAutoRelease} />
                </CalendarSettingRow>
              </div>
            )}

            {activeSection === 'rooms' && (
              <div className="calendar-settings-stack">
                <CalendarSettingRow label="Show capacity labels" desc="Display bed/capacity labels in stay rows.">
                  <CalendarSettingsToggle value={showCapacity} onChange={setShowCapacity} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Show amenities" desc="Show room/stay amenities in details panels.">
                  <CalendarSettingsToggle value={showAmenities} onChange={setShowAmenities} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Airbnb iCal feeds" desc={`${configured}/${rows.length} connected. Sync import is the next backend step.`}>
                  <a className="calendar-settings-link" href="/admin/bookings/calendarfeed/">Feeds</a>
                </CalendarSettingRow>
                <div className="calendar-settings-room-list">
                  {rows.map(({ row, meta }) => (
                    <article key={row.stay.id} style={{ '--room-color': meta.color, '--room-bg': meta.bgColor } as CSSProperties}>
                      <i />
                      <div>
                        <strong>{meta.displayName}</strong>
                        <span>{row.stay.isConfigured ? 'Feed configured' : 'Feed missing'} · {meta.capacityLabel}</span>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}

            {activeSection === 'security' && (
              <div className="calendar-settings-stack">
                <CalendarSettingRow label="Staff-only calendar" desc="Only authenticated staff can open the calendar API.">
                  <span className="calendar-settings-pill">Active</span>
                </CalendarSettingRow>
                <CalendarSettingRow label="Two-factor authentication" desc="Require 2FA for calendar operators.">
                  <CalendarSettingsToggle value={twoFactor} onChange={setTwoFactor} />
                </CalendarSettingRow>
                <CalendarSettingRow label="Session timeout" desc="Auto logout after inactivity.">
                  <select className="calendar-settings-select" defaultValue="60">
                    <option value="30">30 minutes</option>
                    <option value="60">1 hour</option>
                    <option value="240">4 hours</option>
                  </select>
                </CalendarSettingRow>
                <CalendarSettingRow label="Audit trail" desc="Calendar blocks, holds, and price changes remain logged.">
                  <a className="calendar-settings-link" href="/admin/bookings/bookinginquiry/">Audit</a>
                </CalendarSettingRow>
              </div>
            )}
          </section>
        </div>

        <footer className="calendar-settings-panel__footer">
          <button type="button" onClick={onClose}>Cancel</button>
          <button type="button" onClick={onClose}>Save changes</button>
        </footer>
      </aside>
    </div>
  );
}

function CalendarSettingsToggle({ value, onChange }: { value: boolean; onChange: (value: boolean) => void }) {
  return (
    <button
      className={`calendar-settings-toggle-switch ${value ? 'is-active' : ''}`}
      type="button"
      aria-pressed={value}
      onClick={() => onChange(!value)}
    >
      <span />
    </button>
  );
}

function CalendarSettingRow({
  label,
  desc,
  children,
}: {
  label: string;
  desc?: string;
  children: ReactNode;
}) {
  return (
    <article className="calendar-settings-row">
      <div>
        <strong>{label}</strong>
        {desc && <p>{desc}</p>}
      </div>
      <div>{children}</div>
    </article>
  );
}

function CalendarMatrix({
  rows,
  mode,
  search,
  showWeekends,
  focusDate,
  visibleDays,
  dragStart,
  dragEnd,
  onCellMouseDown,
  onCellEnter,
}: {
  rows: StayRowWithMeta[];
  mode: OpsCalendarViewMode;
  search: string;
  showWeekends: boolean;
  focusDate: string;
  visibleDays: OpsCalendarDay[];
  dragStart: GridCellPosition | null;
  dragEnd: GridCellPosition | null;
  onCellMouseDown: (event: MouseEvent<HTMLButtonElement>, rowIndex: number, colIndex: number) => void;
  onCellEnter: (rowIndex: number, colIndex: number) => void;
}) {
  const query = search.trim().toLowerCase();

  return (
    <section
      className={`calendar-booking-grid calendar-booking-grid--${mode}`}
      style={{ '--day-count': visibleDays.length } as CSSProperties}
    >
      <div className="calendar-booking-grid__corner">
        <MapPin size={20} />
        <span>Room / Date</span>
      </div>
      {visibleDays.map((day) => (
        <div
          className={[
            'calendar-booking-grid__date',
            day.isToday ? 'is-today' : '',
            day.inMonth ? '' : 'is-muted',
          ].filter(Boolean).join(' ')}
          key={`date-${day.date}`}
        >
          <span>{day.weekday}</span>
          <strong>{day.day}</strong>
        </div>
      ))}

      {rows.map(({ row, meta }, rowIndex) => {
        const days = daysForWeekendPreference(getRowDays(row, mode, focusDate), showWeekends);
        return (
          <div className="calendar-booking-grid__row" key={row.stay.id} style={{ display: 'contents' }}>
            <article
              className="calendar-booking-grid__stay"
                style={{ '--room-color': meta.color, '--room-bg': meta.bgColor, '--room-text': meta.textColor } as CSSProperties}
            >
              <span className="calendar-booking-grid__rail" />
              <div>
                <Building2 size={22} />
                <strong>{meta.displayName}</strong>
                <small><Users size={15} /> {meta.capacityLabel}</small>
              </div>
            </article>
            {days.map((day, colIndex) => {
              const events = row.events
                .filter((event) => eventCoversDay(event, day.date))
                .filter((event) => !query || [
                  event.title,
                  event.subtitle,
                  event.itemName,
                  event.guestLabel,
                  event.rangeLabel,
                  meta.displayName,
                  meta.shortLabel,
                ].some((value) => value.toLowerCase().includes(query)));
              return (
                <CalendarMatrixCell
                  colIndex={colIndex}
                  day={day}
                  events={events}
                  key={`${row.stay.id}-${day.date}`}
                  meta={meta}
                  mode={mode}
                  rowIndex={rowIndex}
                  selected={selectedGridCoversCell(dragStart, dragEnd, rowIndex, colIndex)}
                  onEnter={onCellEnter}
                  onMouseDown={onCellMouseDown}
                />
              );
            })}
          </div>
        );
      })}
    </section>
  );
}

function CalendarMatrixCell({
  day,
  events,
  selected,
  mode,
  meta,
  rowIndex,
  colIndex,
  onMouseDown,
  onEnter,
}: {
  day: OpsCalendarDay;
  events: OpsCalendarEvent[];
  selected: boolean;
  mode: OpsCalendarViewMode;
  meta: StayVisualMeta;
  rowIndex: number;
  colIndex: number;
  onMouseDown: (event: MouseEvent<HTMLButtonElement>, rowIndex: number, colIndex: number) => void;
  onEnter: (rowIndex: number, colIndex: number) => void;
}) {
  const reservation = events.find((event) => event.type === 'reservation');
  const block = events.find((event) => event.type === 'block');
  const price = events.find((event) => event.type === 'price');
  const primaryEvent = reservation || block || price;

  return (
    <button
      className={[
        'calendar-booking-grid__cell',
        `calendar-booking-grid__cell--${mode}`,
        day.isToday ? 'is-today' : '',
        selected ? 'is-selected' : '',
        day.inMonth ? '' : 'is-muted',
        primaryEvent ? `has-${eventTone(primaryEvent)}` : '',
      ].filter(Boolean).join(' ')}
      type="button"
      onMouseDown={(event) => onMouseDown(event, rowIndex, colIndex)}
      onMouseEnter={() => onEnter(rowIndex, colIndex)}
      onMouseMove={() => onEnter(rowIndex, colIndex)}
      onPointerEnter={() => onEnter(rowIndex, colIndex)}
      onPointerMove={() => onEnter(rowIndex, colIndex)}
      style={{ '--room-color': meta.color, '--room-bg': meta.bgColor } as CSSProperties}
    >
      <strong className="calendar-booking-grid__mobile-date">{day.label}</strong>
      {primaryEvent ? (
        <span className={`calendar-booking-event calendar-booking-event--${eventTone(primaryEvent)}`}>
          {eventLabel(primaryEvent)}
        </span>
      ) : (
        <span className="calendar-booking-available">Available</span>
      )}
      {day.hasPriceOverride && <em>{day.priceDisplay}</em>}
      {events.length > 1 && <small>+{events.length - 1}</small>}
    </button>
  );
}

function CalendarDayDetailsModal({
  rows,
  activeDay,
  initialRow,
  onClose,
}: {
  rows: StayRowWithMeta[];
  activeDay: OpsCalendarDay;
  initialRow: StayRowWithMeta;
  onClose: () => void;
}) {
  const [activeStayId, setActiveStayId] = useState(initialRow.row.stay.id);
  const current = rows.find(({ row }) => row.stay.id === activeStayId) || initialRow;
  const eventsForDay = rows.flatMap(({ row }) => row.events.filter((event) => eventCoversDay(event, activeDay.date)));
  const currentEvents = current.row.events.filter((event) => eventCoversDay(event, activeDay.date));
  const booked = currentEvents.filter((event) => event.type === 'reservation').length;
  const blocked = currentEvents.filter((event) => event.type === 'block').length;
  const price = currentEvents.find((event) => event.type === 'price');
  const isUnavailable = booked > 0 || blocked > 0;

  return (
    <div className="calendar-modal-backdrop" role="dialog" aria-modal="true" aria-label="Day details">
      <section className="calendar-day-modal">
        <header className="calendar-day-modal__header">
          <div>
            <span>Day Details</span>
            <h2>{fullDate(activeDay.date)}</h2>
            <p>{eventsForDay.length} bookings scheduled across all stays</p>
          </div>
          <button type="button" aria-label="Close day details" onClick={onClose}><X size={32} /></button>
        </header>

        <nav className="calendar-day-modal__tabs">
          {rows.map(({ row, meta }) => {
            const tabEvents = row.events.filter((event) => eventCoversDay(event, activeDay.date));
            return (
              <button
                className={row.stay.id === activeStayId ? 'is-active' : ''}
                key={row.stay.id}
                type="button"
                onClick={() => setActiveStayId(row.stay.id)}
                style={{ '--room-color': meta.color } as CSSProperties}
              >
                <span />
                {meta.shortLabel}
                {tabEvents.length > 0 && <em>{tabEvents.length}</em>}
              </button>
            );
          })}
        </nav>

        <div className="calendar-day-modal__body">
          <article
            className="calendar-day-modal__stay-strip"
            style={{ '--room-color': current.meta.color } as CSSProperties}
          >
            <div>
              <MapPin size={25} />
              <strong>{current.meta.displayName}</strong>
            </div>
            <div>
              <span><Users size={22} /> {current.meta.capacityLabel}</span>
              <b>{booked} booked · {blocked} blocked · {isUnavailable ? 'review' : 'available'}</b>
            </div>
          </article>

          <div className="calendar-day-modal__slots">
            {timeSlots.map((slot) => (
              <article className={isUnavailable ? 'is-booked' : 'is-available'} key={slot}>
                <strong><Clock3 size={21} /> {slot}</strong>
                <span>
                  {isUnavailable ? (
                    <>
                      <AlertCircle size={18} />
                      {currentEvents[0]?.title || 'Unavailable'}
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={18} />
                      Available
                    </>
                  )}
                </span>
              </article>
            ))}
          </div>

          {price && (
            <article className="calendar-day-modal__note">
              <DollarSign size={20} />
              <span>{price.title} · {price.amount}</span>
            </article>
          )}
        </div>

        <footer className="calendar-modal-footer">
          <button type="button" onClick={onClose}>Close</button>
        </footer>
      </section>
    </div>
  );
}

function CalendarSelectionModal({
  selectedRows,
  selectedDates,
  onClose,
  onConfirm,
}: {
  selectedRows: StayRowWithMeta[];
  selectedDates: OpsCalendarDay[];
  onClose: () => void;
  onConfirm: (data: BookingDraftFormState) => void;
}) {
  const [form, setForm] = useState<BookingDraftFormState>({
    title: '',
    startTime: '15:00',
    endTime: '12:00',
    bookedBy: '',
    notes: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const totalBookings = selectedRows.length * selectedDates.length;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: Record<string, string> = {};
    if (!form.title.trim()) nextErrors.title = 'Booking title is required';
    if (!form.bookedBy.trim()) nextErrors.bookedBy = 'Booked by is required';
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    onConfirm({
      ...form,
      title: form.title.trim(),
      bookedBy: form.bookedBy.trim(),
      notes: form.notes.trim(),
    });
  }

  return (
    <div className="calendar-modal-backdrop" role="dialog" aria-modal="true" aria-label="New booking">
      <section className="calendar-selection-modal">
        <header className="calendar-selection-modal__header">
          <div>
            <h2>New Booking</h2>
            <p>{totalBookings} booking{totalBookings === 1 ? '' : 's'} will be created</p>
          </div>
          <button type="button" aria-label="Close new booking" onClick={onClose}><X size={30} /></button>
        </header>

        <article className="calendar-selection-modal__summary">
          <div>
            <MapPin size={24} />
            <span>
              {selectedRows.map(({ row, meta }) => (
                <b key={row.stay.id} style={{ '--room-color': meta.color } as CSSProperties}>{meta.shortLabel}</b>
              ))}
            </span>
          </div>
          <div>
            <CalendarDays size={24} />
            <strong>{dateRangeLabel(selectedDates)}</strong>
          </div>
        </article>

        <form onSubmit={submit}>
          <label>
            <span>Booking Title *</span>
            <input
              className={errors.title ? 'has-error' : ''}
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              placeholder="e.g. Direct guest hold, owner stay, maintenance..."
            />
          </label>

          <div className="calendar-selection-modal__time">
            <label>
              <span><Clock3 size={20} /> Check-in / start</span>
              <input
                value={form.startTime}
                onChange={(event) => setForm({ ...form, startTime: event.target.value })}
                type="time"
              />
            </label>
            <label>
              <span>Check-out / end</span>
              <input
                value={form.endTime}
                onChange={(event) => setForm({ ...form, endTime: event.target.value })}
                type="time"
              />
            </label>
          </div>

          <label>
            <span>Booked By *</span>
            <input
              className={errors.bookedBy ? 'has-error' : ''}
              value={form.bookedBy}
              onChange={(event) => setForm({ ...form, bookedBy: event.target.value })}
              placeholder="Guest, owner, platform, or team member"
            />
          </label>

          <label>
            <span>Notes (optional)</span>
            <textarea
              value={form.notes}
              onChange={(event) => setForm({ ...form, notes: event.target.value })}
              placeholder="Additional details, source, payment status, or internal notes..."
            />
          </label>

          <footer className="calendar-modal-footer">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit">Confirm ({totalBookings})</button>
          </footer>
        </form>
      </section>
    </div>
  );
}

function EventList({ events, onDelete }: { events: OpsCalendarEvent[]; onDelete: (event: OpsCalendarEvent) => void }) {
  if (events.length === 0) {
    return (
      <article className="ops-calendar-empty">
        <Sparkles size={24} />
        <h3>No matching calendar records.</h3>
        <p>Adjust search, switch date range, or create a new booking hold.</p>
      </article>
    );
  }

  return (
    <div className="ops-calendar-list">
      {events.map((event) => (
        <article className={`ops-calendar-list-row ops-calendar-list-row--${eventTone(event)}`} key={event.id}>
          <div>
            <span>{event.subtitle}</span>
            <strong>{event.title}</strong>
            <p>{event.itemName ? lockedStayIdentity(event.itemName, '', 0).displayName : 'Calendar record'} · {event.rangeLabel} {event.guestLabel ? `· ${event.guestLabel}` : ''}</p>
          </div>
          <div>
            {event.amount && <strong>{event.amount}</strong>}
            <a href={event.adminUrl}>Record <ExternalLink size={13} /></a>
            {event.type !== 'reservation' && (
              <button type="button" onClick={() => onDelete(event)}>
                <Trash2 size={14} /> Delete
              </button>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
