import { AgentMode, DepositStatus, ReservationStatus } from '../../domain/models';

type BadgeTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'premium';

interface StatusBadgeProps {
  label: string;
  tone?: BadgeTone;
}

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

export function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{label}</span>;
}
