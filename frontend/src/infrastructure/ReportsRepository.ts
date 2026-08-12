import {
  ReportChart,
  ReportChartRow,
  ReportMetric,
  ReportMetricTone,
  ReportWorkspace,
} from '../domain/reports';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';
import type { OpsWorkspaceRepository } from './OpsWorkspaceRepository';

const TONES: ReportMetricTone[] = ['green', 'cyan', 'violet', 'orange', 'red'];

function formatDate(value: string) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
}

function emptyReportWorkspace(reason = 'reports API snapshot'): ReportWorkspace {
  return new ReportWorkspace(
    [],
    [],
    'No report period available',
    'Waiting for live report data',
    null,
    createWorkspaceMetadata('fallback', [reason]),
  );
}

export class ReportsRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  fallback(): ReportWorkspace {
    return emptyReportWorkspace();
  }

  async getWorkspace(): Promise<ReportWorkspace> {
    try {
      const snapshot = await this.opsRepository.getReports();
      const metrics = snapshot.summaryCards.map((metric, index) => new ReportMetric(
        metric.label,
        String(metric.value),
        metric.caption,
        TONES[index % TONES.length],
      ));
      const charts = snapshot.charts.map((chart) => new ReportChart(
        chart.id,
        chart.title,
        chart.category,
        chart.rows.map((row) => new ReportChartRow(row.label, row.total, row.width)),
      ));

      return new ReportWorkspace(
        metrics,
        charts,
        `${formatDate(snapshot.reportSince)} - ${formatDate(snapshot.reportUntil)}`,
        `Generated from live operational records through ${formatDate(snapshot.reportUntil)}`,
        snapshot,
        createWorkspaceMetadata('api'),
      );
    } catch {
      return emptyReportWorkspace('The live reports endpoint could not be loaded.');
    }
  }
}
