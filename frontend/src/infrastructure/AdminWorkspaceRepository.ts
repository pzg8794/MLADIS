import {
  AdminFeedItem,
  AdminHealthCard,
  AdminMetric,
  AdminShortcut,
  AdminWorkspace,
} from '../domain/admin';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';
import type { OpsWorkspaceRepository } from './OpsWorkspaceRepository';

function fallbackAdminWorkspace(source: 'fallback' | 'mixed' = 'fallback'): AdminWorkspace {
  return new AdminWorkspace(
    [
      new AdminShortcut('Records', 'Master data, settings, and system records.', '/ops/admin/', 'database', 'Open', 'blue'),
      new AdminShortcut('Reservations', 'Manage bookings, requests, and confirmations.', '/ops/reservations/', 'calendar', 'Manage', 'teal'),
      new AdminShortcut('Guests / Customers', 'Profiles, communications, and guest history.', '/ops/customers/', 'users', 'View', 'violet'),
      new AdminShortcut('Properties', 'Inventory, details, photos, and configurations.', '/ops/properties/', 'box', 'Manage', 'blue'),
      new AdminShortcut('Calendar', 'Availability, pricing, blocks, and overrides.', '/ops/calendar/', 'calendar', 'Open', 'teal'),
      new AdminShortcut('Maintenance', 'Issues, inspections, and preventive maintenance.', '/ops/maintenance/', 'wrench', 'View', 'amber'),
      new AdminShortcut('Work Orders', 'Track assignments, status, and completion.', '/ops/maintenance/', 'clipboard', 'Open', 'amber'),
      new AdminShortcut('Payments', 'Transactions, refunds, and reconciliation.', '/ops/payments/', 'dollar', 'Open', 'blue'),
      new AdminShortcut('Deposits', 'Holds, releases, and deposit management.', '/ops/deposits/', 'shield', 'Open', 'rose'),
      new AdminShortcut('Reports', 'Operational charts, KPIs, and exports.', '/ops/reports/', 'trend', 'View', 'blue'),
      new AdminShortcut('Brand Settings', 'Logo, contacts, policies, and brand assets.', '/ops/settings/', 'settings', 'Manage', 'violet'),
      new AdminShortcut('Agent FAQ', 'Guest & agent training, answers, and resources.', '/ops/settings/', 'message', 'Manage', 'rose'),
      new AdminShortcut('Users', 'Team members, roles, and permissions.', '/ops/admin/', 'users', 'Manage', 'violet'),
      new AdminShortcut('OAuth / Integrations', 'API, webhooks, and connected services.', '/ops/settings/', 'radio', 'Manage', 'teal'),
    ],
    [
      new AdminMetric('Active stays', '128', '+ 12% vs yesterday', 'box', 'violet'),
      new AdminMetric('Pending requests', '23', '+ 5 new', 'clock', 'amber'),
      new AdminMetric('Deposit holds', '$74,560', '12 holds', 'shield', 'teal'),
      new AdminMetric('Open tasks', '18', '- 3 completed', 'clipboard', 'blue'),
    ],
    [
      new AdminFeedItem('2m ago', 'New reservation created', '#R-58291 - Ocean View Villa - Aug 12 - 16', 'calendar', 'blue'),
      new AdminFeedItem('7m ago', 'Deposit captured', '$2,450.00 - #R-58288 - Beach House', 'shield', 'green'),
      new AdminFeedItem('16m ago', 'Maintenance issue reported', 'AC not cooling - Unit 3B - High priority', 'wrench', 'amber'),
      new AdminFeedItem('28m ago', 'Guest message received', 'Late check-in request - #R-58285', 'message', 'cyan'),
      new AdminFeedItem('35m ago', 'Payment refunded', '$125.00 - #R-58262 - Cancellation', 'dollar', 'green'),
    ],
    [
      new AdminHealthCard('Staff access', 'Staff only', 'Protected', 'users', 'slate'),
      new AdminHealthCard('Controlled edits', 'Enabled', 'Audit on', 'trend', 'green'),
      new AdminHealthCard('Build status', 'Production', 'v2.4.17', 'clipboard', 'blue'),
      new AdminHealthCard('Last backup', 'Today, 3:14 AM', 'Automated', 'database', 'teal'),
    ],
    createWorkspaceMetadata(source, source === 'fallback' ? ['admin API snapshot'] : ['workspace shortcuts']),
  );
}

export class AdminWorkspaceRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  fallback(): AdminWorkspace {
    return fallbackAdminWorkspace();
  }

  async getWorkspace(): Promise<AdminWorkspace> {
    try {
      const snapshot = await this.opsRepository.getAdmin();
      const fallback = fallbackAdminWorkspace('mixed');
      const metrics = fallback.metrics.map((metric, index) => {
        const apiMetric = snapshot.summaryCards[index];
        if (!apiMetric) return metric;
        return new AdminMetric(apiMetric.label, apiMetric.value, apiMetric.caption, metric.iconKey, metric.tone);
      });
      return new AdminWorkspace(
        fallback.shortcuts,
        metrics,
        fallback.feedItems,
        fallback.healthCards,
        createWorkspaceMetadata('mixed', ['shortcut/feed/health projections']),
      );
    } catch {
      return fallbackAdminWorkspace();
    }
  }
}
