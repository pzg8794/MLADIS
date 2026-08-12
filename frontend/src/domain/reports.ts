import type { OpsReportsSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type ReportMetricTone = 'green' | 'cyan' | 'violet' | 'orange' | 'red';

export class ReportMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly tone: ReportMetricTone,
  ) {}
}

export class ReportChartRow {
  constructor(
    public readonly label: string,
    public readonly total: number,
    public readonly width: number,
  ) {}
}

export class ReportChart {
  constructor(
    public readonly id: string,
    public readonly title: string,
    public readonly category: string,
    public readonly rows: ReportChartRow[],
  ) {}

  get hasData() {
    return this.rows.some((row) => row.total > 0);
  }
}

export class ReportWorkspace {
  constructor(
    public readonly metrics: ReportMetric[],
    public readonly charts: ReportChart[],
    public readonly dateRangeLabel: string,
    public readonly generatedAtLabel: string,
    public readonly sourceSnapshot: OpsReportsSnapshot | null,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('fallback'),
  ) {}

  get source() {
    return this.metadata.source;
  }

  chart(id: string) {
    return this.charts.find((chart) => chart.id === id) ?? null;
  }

  visibleCharts(limit = 9) {
    const populated = this.charts.filter((chart) => chart.hasData);
    return (populated.length ? populated : this.charts).slice(0, limit);
  }
}
