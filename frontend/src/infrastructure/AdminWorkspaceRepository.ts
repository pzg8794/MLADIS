import {
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
    [],
    [],
    [],
    createWorkspaceMetadata(source, source === 'fallback' ? ['admin API unavailable'] : []),
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
      const iconKeys = ['users', 'shield', 'users', 'clipboard', 'database', 'clock'];
      const tones: Array<'blue' | 'violet' | 'teal' | 'amber' | 'rose'> = ['blue', 'teal', 'violet', 'blue', 'amber', 'rose'];
      const metrics = snapshot.summaryCards.map((metric, index) => new AdminMetric(
        metric.label,
        metric.value,
        metric.caption,
        iconKeys[index] ?? 'shield',
        tones[index] ?? 'blue',
      ));
      return new AdminWorkspace(
        fallback.shortcuts,
        metrics,
        fallback.feedItems,
        fallback.healthCards,
        createWorkspaceMetadata('api'),
      );
    } catch {
      return fallbackAdminWorkspace();
    }
  }
}
