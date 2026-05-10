export type TrendDirection = 'up' | 'down' | 'neutral';
export type ReservationStatus = 'new' | 'reviewing' | 'confirmed' | 'cancelled' | 'completed';
export type DepositStatus = 'pending' | 'authorized' | 'captured' | 'released' | 'failed';
export type AgentMode = 'faq' | 'openai' | 'fallback';

export class Money {
  constructor(
    public readonly cents: number,
    public readonly currency: string = 'USD',
  ) {}

  format(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency,
      maximumFractionDigits: 0,
    }).format(this.cents / 100);
  }
}

export class DashboardMetric {
  constructor(
    public readonly id: string,
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly trend: TrendDirection = 'neutral',
    public readonly trendLabel: string = 'Stable',
  ) {}
}

export class ReservationSummary {
  constructor(
    public readonly id: number,
    public readonly guestName: string,
    public readonly stayName: string,
    public readonly checkIn: string,
    public readonly checkOut: string,
    public readonly guests: number,
    public readonly status: ReservationStatus,
    public readonly actionRequired: boolean = false,
  ) {}
}

export class DepositSummary {
  constructor(
    public readonly id: number,
    public readonly guestName: string,
    public readonly stayName: string,
    public readonly amount: Money,
    public readonly provider: 'Stripe' | 'PayPal',
    public readonly status: DepositStatus,
  ) {}
}

export class AgentQuestionSummary {
  constructor(
    public readonly id: number,
    public readonly topic: string,
    public readonly lastQuestion: string,
    public readonly mode: AgentMode,
    public readonly createdAt: string,
  ) {}
}

export class CalendarAlert {
  constructor(
    public readonly id: string,
    public readonly label: string,
    public readonly stayName: string,
    public readonly dateRange: string,
    public readonly severity: 'info' | 'warning' | 'danger' = 'info',
  ) {}
}

export class DashboardSnapshot {
  constructor(
    public readonly metrics: DashboardMetric[],
    public readonly reservations: ReservationSummary[],
    public readonly deposits: DepositSummary[],
    public readonly agentQuestions: AgentQuestionSummary[],
    public readonly calendarAlerts: CalendarAlert[],
    public readonly generatedAt: string,
    public readonly source: 'api' | 'mock' = 'mock',
  ) {}
}
