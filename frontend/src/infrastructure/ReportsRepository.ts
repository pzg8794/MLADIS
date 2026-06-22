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

const BASE = import.meta.env.BASE_URL;

function fallbackReportWorkspace(source: 'fallback' | 'mixed' = 'fallback'): ReportWorkspace {
  return new ReportWorkspace(
    [
      new ReportMetric('Revenue', '$18,540', '+15% vs Jun 29 - Jul 5', 'revenue', 'green', [9, 10, 9, 11, 10, 12, 13, 11, 12, 13, 12, 14]),
      new ReportMetric('Occupancy', '72%', '+5pp vs Jun 29 - Jul 5', 'occupancy', 'cyan', [7, 8, 8, 9, 10, 9, 8, 7, 8, 9, 8, 8]),
      new ReportMetric('ADR (Avg. Daily Rate)', '$132', '+7% vs Jun 29 - Jul 5', 'adr', 'violet', [8, 9, 8, 9, 8, 10, 11, 10, 9, 10, 9, 10]),
      new ReportMetric('Guest Rating', '4.93 / 5', '+0.05 vs Jun 29 - Jul 5', 'rating', 'orange', [9, 9, 10, 9, 10, 10, 9, 10, 9, 10, 9, 10]),
      new ReportMetric('Maintenance Cost', '$2,310', '-6% vs Jun 29 - Jul 5', 'maintenance', 'red', [7, 8, 8, 7, 8, 7, 8, 8, 7, 8, 7, 7]),
    ],
    new ReportRevenueSeries(
      [8, 11, 14.5, 13, 16, 18, 18.5],
      [5, 7, 8, 9, 10, 11, 14],
      ['Jun 6', 'Jun 7', 'Jun 8', 'Jun 9', 'Jun 10', 'Jun 11', 'Jun 12'],
    ),
    [
      new ReportChannelRow('Direct Website', 42, 26, 'is-42'),
      new ReportChannelRow('Airbnb', 28, 17, 'is-28'),
      new ReportChannelRow('Booking.com', 16, 10, 'is-16'),
      new ReportChannelRow('Vrbo', 8, 5, 'is-8'),
      new ReportChannelRow('Other', 6, 4, 'is-6'),
    ],
    [
      new ReportListingShare('6 Beds Apt, Vacation Home & Pool, G-101', 34, '$6,304', 'is-blue'),
      new ReportListingShare('2 Beds Apt, Vacation Home & Pool', 26, '$4,816', 'is-violet'),
      new ReportListingShare('3 Beds Apt, Vacation Home & Pool, G-101', 20, '$3,708', 'is-orange'),
      new ReportListingShare('Meeting Room 1', 8, '$1,482', 'is-red'),
      new ReportListingShare('Others', 12, '$2,230', 'is-gray'),
    ],
    [
      new ReportHeatDay(31, 0), new ReportHeatDay(1, 1), new ReportHeatDay(2, 2),
      new ReportHeatDay(3, 3), new ReportHeatDay(4, 3), new ReportHeatDay(5, 4),
      new ReportHeatDay(6, 5), new ReportHeatDay(7, 1), new ReportHeatDay(8, 2),
      new ReportHeatDay(9, 3), new ReportHeatDay(10, 4), new ReportHeatDay(11, 4),
      new ReportHeatDay(12, 5), new ReportHeatDay(13, 5), new ReportHeatDay(14, 2),
      new ReportHeatDay(15, 2), new ReportHeatDay(16, 3), new ReportHeatDay(17, 4),
      new ReportHeatDay(18, 4), new ReportHeatDay(19, 5), new ReportHeatDay(20, 5),
      new ReportHeatDay(21, 2), new ReportHeatDay(22, 2), new ReportHeatDay(23, 3),
      new ReportHeatDay(24, 4), new ReportHeatDay(25, 4), new ReportHeatDay(26, 5),
      new ReportHeatDay(27, 5), new ReportHeatDay(28, 2), new ReportHeatDay(29, 1),
      new ReportHeatDay(30, 1), new ReportHeatDay(1, 0),
    ],
    [
      new ReportInsight('Revenue is up 15%', 'You earned $18,540 this week, up 15% compared to Jun 29 - Jul 5.', 'green', 'trend'),
      new ReportInsight('Direct bookings are growing', 'Direct website bookings increased 12% and now represent 42% of total bookings.', 'blue', 'link'),
      new ReportInsight('Occupancy dips on weekdays', 'Tuesday and Wednesday show the lowest occupancy (58%). Consider promotions to boost midweek demand.', 'orange', 'warning'),
    ],
    [
      new ReportStayRow('6 Beds Apt, Vacation Home & Pool, G-101', 'Apt #16 - 5 beds', '$6,304', '78%', '$146', '4.97', '+2', 'tc-blue', `${BASE}stays/stay-6br.jpg`),
      new ReportStayRow('2 Beds Apt, Vacation Home & Pool', 'Apt #7 - 2 beds', '$4,816', '71%', '$128', '4.92', '-', 'tc-violet', `${BASE}stays/stay-2br.jpg`),
      new ReportStayRow('3 Beds Apt, Vacation Home & Pool, G-101', 'Apt #13 - 3 beds', '$3,708', '69%', '$116', '4.90', '+1', 'tc-orange', `${BASE}stays/stay-3br.jpg`),
      new ReportStayRow('Meeting Room 1', 'Conference space', '$1,482', '62%', '$89', '4.85', '+1', 'tc-red', `${BASE}stays/stay-3br.jpg`),
      new ReportStayRow('Conference Room A', 'Meeting room - seats 8', '$1,205', '58%', '$76', '4.70', '+1', 'tc-slate', `${BASE}stays/stay-2br.jpg`),
    ],
    'Jun 6 - Jun 12, 2026',
    null,
    createWorkspaceMetadata(source, source === 'fallback' ? ['reports API snapshot'] : ['chart projections']),
  );
}

export class ReportsRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  fallback(): ReportWorkspace {
    return fallbackReportWorkspace();
  }

  async getWorkspace(): Promise<ReportWorkspace> {
    try {
      const snapshot = await this.opsRepository.getReports();
      const fallback = fallbackReportWorkspace('mixed');
      const metrics = fallback.metrics.map((metric, index) => {
        const apiMetric = snapshot.summaryCards[index];
        if (!apiMetric) return metric;
        return new ReportMetric(
          apiMetric.label,
          apiMetric.value,
          apiMetric.caption,
          metric.iconKey,
          metric.tone,
          metric.spark,
        );
      });

      return new ReportWorkspace(
        metrics,
        fallback.revenueSeries,
        fallback.channels,
        fallback.listings,
        fallback.heatDays,
        fallback.insights,
        fallback.stays,
        `${snapshot.reportSince} - ${snapshot.reportUntil}`,
        snapshot,
        createWorkspaceMetadata('mixed', ['chart projections']),
      );
    } catch {
      return fallbackReportWorkspace();
    }
  }
}
