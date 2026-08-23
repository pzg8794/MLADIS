import type { OpsReportsSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type ReportMetricTone = 'green' | 'cyan' | 'violet' | 'orange' | 'red';
export type ReportInsightTone = 'green' | 'blue' | 'orange';

export class ReportMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly delta: string,
    public readonly iconKey: 'revenue' | 'occupancy' | 'adr' | 'rating' | 'maintenance',
    public readonly tone: ReportMetricTone,
    public readonly spark: number[],
  ) {}
}

export class ReportRevenueSeries {
  constructor(
    public readonly title: string,
    public readonly current: number[],
    public readonly previous: number[],
    public readonly labels: string[],
    public readonly valuePrefix: string = '',
    public readonly valueSuffix: string = '',
  ) {}
}

export class ReportChannelRow {
  constructor(
    public readonly label: string,
    public readonly pct: number,
    public readonly bookings: number,
    public readonly widthClass: string,
  ) {}
}

export class ReportListingShare {
  constructor(
    public readonly label: string,
    public readonly pct: number,
    public readonly amount: string,
    public readonly toneClass: string,
    public readonly color: string,
  ) {}
}

export class ReportHeatDay {
  constructor(
    public readonly day: number,
    public readonly intensity: number,
  ) {}
}

export class ReportInsight {
  constructor(
    public readonly title: string,
    public readonly body: string,
    public readonly tone: ReportInsightTone,
    public readonly iconKey: 'trend' | 'link' | 'warning',
  ) {}
}

export class ReportStayRow {
  constructor(
    public readonly listing: string,
    public readonly sub: string,
    public readonly revenue: string,
    public readonly occ: string,
    public readonly adr: string,
    public readonly rating: string,
    public readonly delta: string,
    public readonly toneClass: string,
    public readonly imgSrc: string,
  ) {}
}

export class ReportWorkspace {
  constructor(
    public readonly metrics: ReportMetric[],
    public readonly revenueSeries: ReportRevenueSeries,
    public readonly channels: ReportChannelRow[],
    public readonly listings: ReportListingShare[],
    public readonly heatDays: ReportHeatDay[],
    public readonly insights: ReportInsight[],
    public readonly stays: ReportStayRow[],
    public readonly dateRangeLabel: string,
    public readonly heroSubtitle: string,
    public readonly channelTitle: string,
    public readonly listingTitle: string,
    public readonly listingTotalLabel: string,
    public readonly listingNote: string,
    public readonly heatmapTitle: string,
    public readonly heatmapPeriodLabel: string,
    public readonly staysTitle: string,
    public readonly stayColumnLabels: readonly [string, string, string, string, string, string],
    public readonly staysCountLabel: string,
    public readonly insightsTitle: string,
    public readonly sourceSnapshot: OpsReportsSnapshot | null,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('fallback'),
  ) {}

  get source() {
    return this.metadata.source;
  }
}
