import { AgentMode, DepositStatus, ReservationStatus } from '../../domain/models';
import { BadgeTone } from './StatusBadge';

const statusToneMap: Record<string, BadgeTone> = {
  new: 'info',
  reviewing: 'warning',
  confirmed: 'success',
  cancelled: 'danger',
  completed: 'neutral',
  pending: 'warning',
  authorized: 'success',
  captured: 'premium',
  released: 'neutral',
  failed: 'danger',
  faq: 'success',
  openai: 'premium',
  fallback: 'warning',
};

export class StatusBadgePresenter {
  static toneForStatus(status: ReservationStatus | DepositStatus | AgentMode | string): BadgeTone {
    return statusToneMap[status] ?? 'neutral';
  }

  static labelForStatus(status: string): string {
    return status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  }
}
