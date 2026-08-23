import type { OpsChart, OpsChartRow, OpsReportsSnapshot } from '../domain/models';
import {
  ReportChannelRow,
  ReportHeatDay,
  ReportInsight,
  ReportListingShare,
  ReportMetric,
  ReportRevenueSeries,
  ReportStayRow,
  ReportWorkspace,
} from '../domain/reports';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';
import type { OpsWorkspaceRepository } from './OpsWorkspaceRepository';

const METRIC_SPECS = [
  { label: 'Reservations', icon: 'revenue', tone: 'green', chartId: 'booking_timeline' },
  { label: '30-day inquiries', icon: 'occupancy', tone: 'cyan', chartId: 'booking_timeline' },
  { label: 'Visits', icon: 'adr', tone: 'violet', chartId: 'visit_timeline' },
  { label: 'Agent chats', icon: 'rating', tone: 'orange', chartId: 'agent_topic_chart' },
  { label: 'Active listings', icon: 'maintenance', tone: 'red', chartId: 'booking_category_chart' },
] as const;

const LISTING_COLORS = ['#2563eb', '#7c3aed', '#ea580c', '#dc2626', '#64748b'];
const LISTING_TONES = ['is-blue', 'is-violet', 'is-orange', 'is-red', 'is-gray'];

function emptyReportWorkspace(reason = 'reports API snapshot'): ReportWorkspace {
  return new ReportWorkspace(
    [],
    new ReportRevenueSeries('Reservation Requests Over Time', [], [], []),
    [],
    [],
    [],
    [],
    [],
    'Report period unavailable',
    'Track verified reservations, demand, traffic, customer signals, payments, and agent activity.',
    'Reservations by Status',
    'Reservation Mix by Listing',
    '0',
    'Based on captured reservation records',
    'Reservation Demand Heatmap',
    'No report period',
    'Top Reservation Demand',
    ['Stay / Listing', 'Requests', 'Share', 'Rank', 'Source', 'Status'],
    'No stay-specific reservation records',
    'Operational Insights',
    null,
    createWorkspaceMetadata('fallback', [reason]),
  );
}

function chart(snapshot: OpsReportsSnapshot, id: string): OpsChart | null {
  return snapshot.charts.find((candidate) => candidate.id === id) ?? null;
}

function populatedRows(source: OpsChart | null): OpsChartRow[] {
  return (source?.rows ?? []).filter((row) => row.total > 0);
}

function formatDate(value: string): string {
  const isoDay = value.slice(0, 10);
  const date = new Date(`${isoDay}T12:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
}

function buildMetrics(snapshot: OpsReportsSnapshot): ReportMetric[] {
  const summaries = new Map(snapshot.summaryCards.map((metric) => [metric.label, metric]));
  return METRIC_SPECS.flatMap((spec) => {
    const metric = summaries.get(spec.label);
    if (!metric) return [];
    const spark = (chart(snapshot, spec.chartId)?.rows ?? []).map((row) => row.total).slice(-12);
    return [new ReportMetric(metric.label, metric.value, metric.caption, spec.icon, spec.tone, spark)];
  });
}

function buildTrend(snapshot: OpsReportsSnapshot): ReportRevenueSeries {
  const rows = chart(snapshot, 'booking_timeline')?.rows ?? [];
  const periodSize = Math.floor(rows.length / 2);
  if (!periodSize) return new ReportRevenueSeries('Reservation Requests Over Time', [], [], []);
  const previousRows = rows.slice(0, periodSize);
  const currentRows = rows.slice(-periodSize);
  return new ReportRevenueSeries(
    'Reservation Requests Over Time',
    currentRows.map((row) => row.total),
    previousRows.map((row) => row.total),
    currentRows.map((row) => row.label),
  );
}

function buildChannels(snapshot: OpsReportsSnapshot): ReportChannelRow[] {
  const rows = populatedRows(chart(snapshot, 'reservation_status_chart'));
  const total = rows.reduce((sum, row) => sum + row.total, 0);
  return rows.map((row) => {
    const pct = total ? Math.round((row.total / total) * 100) : 0;
    return new ReportChannelRow(row.label, pct, row.total, `is-${pct}`);
  });
}

function buildListings(snapshot: OpsReportsSnapshot): ReportListingShare[] {
  const rows = populatedRows(chart(snapshot, 'item_chart')).slice(0, 5);
  const total = rows.reduce((sum, row) => sum + row.total, 0);
  return rows.map((row, index) => new ReportListingShare(
    row.label,
    total ? Math.round((row.total / total) * 100) : 0,
    `${row.total.toLocaleString()} request${row.total === 1 ? '' : 's'}`,
    LISTING_TONES[index % LISTING_TONES.length],
    LISTING_COLORS[index % LISTING_COLORS.length],
  ));
}

function buildHeatDays(snapshot: OpsReportsSnapshot): ReportHeatDay[] {
  const rows = chart(snapshot, 'booking_timeline')?.rows ?? [];
  const max = Math.max(...rows.map((row) => row.total), 0);
  const firstDate = new Date(`${snapshot.reportSince.slice(0, 10)}T12:00:00`);
  const leading = Number.isNaN(firstDate.getTime()) ? 0 : firstDate.getDay();
  const cells = rows.map((row) => {
    const day = Number.parseInt(row.label.replace(/^\D+/, ''), 10) || 0;
    const intensity = max && row.total ? Math.max(1, Math.ceil((row.total / max) * 5)) : 0;
    return new ReportHeatDay(day, intensity);
  });
  const trailing = (7 - ((leading + cells.length) % 7)) % 7;
  return [
    ...Array.from({ length: leading }, () => new ReportHeatDay(0, 0)),
    ...cells,
    ...Array.from({ length: trailing }, () => new ReportHeatDay(0, 0)),
  ];
}

function buildStays(snapshot: OpsReportsSnapshot): ReportStayRow[] {
  const rows = populatedRows(chart(snapshot, 'item_chart')).slice(0, 5);
  const total = rows.reduce((sum, row) => sum + row.total, 0);
  return rows.map((row, index) => new ReportStayRow(
    row.label,
    'Captured reservation records',
    row.total.toLocaleString(),
    `${total ? Math.round((row.total / total) * 100) : 0}%`,
    `#${index + 1}`,
    'Bookings DB',
    'Live',
    `tc-${['blue', 'violet', 'orange', 'red', 'slate'][index % 5]}`,
    '',
  ));
}

function buildInsights(
  trend: ReportRevenueSeries,
  channels: ReportChannelRow[],
  listings: ReportListingShare[],
): ReportInsight[] {
  const currentTotal = trend.current.reduce((sum, value) => sum + value, 0);
  const previousTotal = trend.previous.reduce((sum, value) => sum + value, 0);
  const change = previousTotal ? Math.round(((currentTotal - previousTotal) / previousTotal) * 100) : null;
  const trendTitle = change === null
    ? `${currentTotal.toLocaleString()} request${currentTotal === 1 ? '' : 's'} in the current period`
    : `Reservation demand ${change >= 0 ? 'rose' : 'fell'} ${Math.abs(change)}%`;
  const trendBody = change === null
    ? 'The comparison period contains no reservation requests.'
    : `${currentTotal.toLocaleString()} requests were recorded versus ${previousTotal.toLocaleString()} in the preceding period.`;
  const insights = [new ReportInsight(
    trendTitle,
    trendBody,
    change !== null && change < 0 ? 'orange' : 'green',
    change !== null && change < 0 ? 'warning' : 'trend',
  )];

  const leadingStatus = [...channels].sort((left, right) => right.bookings - left.bookings)[0];
  if (leadingStatus) {
    insights.push(new ReportInsight(
      `${leadingStatus.label} is the leading status`,
      `${leadingStatus.bookings.toLocaleString()} reservation${leadingStatus.bookings === 1 ? '' : 's'} (${leadingStatus.pct}%) currently ${leadingStatus.bookings === 1 ? 'has' : 'have'} this status.`,
      'blue',
      'link',
    ));
  }

  const topListing = listings[0];
  if (topListing) {
    insights.push(new ReportInsight(
      'Highest recorded listing demand',
      `${topListing.label} represents ${topListing.pct}% of stay-specific reservation requests.`,
      'orange',
      'warning',
    ));
  }
  return insights;
}

export class ReportsRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  fallback(): ReportWorkspace {
    return emptyReportWorkspace();
  }

  async getWorkspace(): Promise<ReportWorkspace> {
    try {
      const snapshot = await this.opsRepository.getReports();
      const trend = buildTrend(snapshot);
      const channels = buildChannels(snapshot);
      const listings = buildListings(snapshot);
      const stays = buildStays(snapshot);
      const reportRange = `${formatDate(snapshot.reportSince)} - ${formatDate(snapshot.reportUntil)}`;
      const listingTotal = populatedRows(chart(snapshot, 'item_chart'))
        .reduce((sum, row) => sum + row.total, 0);

      return new ReportWorkspace(
        buildMetrics(snapshot),
        trend,
        channels,
        listings,
        buildHeatDays(snapshot),
        buildInsights(trend, channels, listings),
        stays,
        reportRange,
        'Track verified reservations, demand, traffic, customer signals, payments, and agent activity.',
        'Reservations by Status',
        'Reservation Mix by Listing',
        listingTotal.toLocaleString(),
        'Based on captured reservation records',
        'Reservation Demand Heatmap',
        reportRange,
        'Top Reservation Demand',
        ['Stay / Listing', 'Requests', 'Share', 'Rank', 'Source', 'Status'],
        stays.length ? `Showing ${stays.length} stay${stays.length === 1 ? '' : 's'} with recorded demand` : 'No stay-specific reservation records',
        'Operational Insights',
        snapshot,
        createWorkspaceMetadata('api'),
      );
    } catch {
      return emptyReportWorkspace('The live reports endpoint could not be loaded.');
    }
  }
}
