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
    public readonly accent: 'teal' | 'blue' | 'violet' | 'amber' | 'rose' = 'teal',
    public readonly progress: number = 0,
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

export class StayPerformance {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly subtitle: string,
    public readonly imageUrl: string,
    public readonly rating: string,
    public readonly occupancyLabel: string,
    public readonly revenueLabel: string,
    public readonly status: 'live' | 'review' | 'blocked' = 'live',
  ) {}
}

export class DashboardSnapshot {
  constructor(
    public readonly metrics: DashboardMetric[],
    public readonly reservations: ReservationSummary[],
    public readonly deposits: DepositSummary[],
    public readonly agentQuestions: AgentQuestionSummary[],
    public readonly calendarAlerts: CalendarAlert[],
    public readonly stays: StayPerformance[],
    public readonly generatedAt: string,
    public readonly source: 'api' | 'mock' = 'mock',
  ) {}
}

export class PublicReviewHighlight {
  constructor(
    public readonly title: string,
    public readonly body: string,
    public readonly sourceLabel: string,
  ) {}
}

export class PublicHouseRule {
  constructor(
    public readonly title: string,
    public readonly description: string,
  ) {}
}

export class PublicGalleryImage {
  constructor(
    public readonly imageUrl: string,
    public readonly altText: string,
    public readonly caption: string,
  ) {}
}

export class PublicStay {
  constructor(
    public readonly id: number,
    public readonly name: string,
    public readonly slug: string,
    public readonly headline: string,
    public readonly description: string,
    public readonly location: string,
    public readonly imageUrl: string,
    public readonly rating: string,
    public readonly reviewLabel: string,
    public readonly priceLabel: string,
    public readonly statList: string[],
    public readonly detailUrl: string,
    public readonly airbnbUrl: string,
    public readonly gallery: PublicGalleryImage[],
    public readonly highlights: PublicReviewHighlight[],
    public readonly rules: PublicHouseRule[],
  ) {}
}

export class AreaTile {
  constructor(
    public readonly title: string,
    public readonly caption: string,
    public readonly imageUrl: string,
  ) {}
}

export class MissionCauseSummary {
  constructor(
    public readonly title: string,
    public readonly description: string,
  ) {}
}

export class PublicSiteSnapshot {
  constructor(
    public readonly siteName: string,
    public readonly logoUrl: string,
    public readonly contactEmail: string,
    public readonly publicAddressLabel: string,
    public readonly depositAmount: string,
    public readonly stays: PublicStay[],
    public readonly areaTiles: AreaTile[],
    public readonly missionCauses: MissionCauseSummary[],
    public readonly generatedAt: string,
    public readonly source: 'api' | 'mock' = 'api',
  ) {}
}

export class AccountReservation {
  constructor(
    public readonly id: number,
    public readonly guestName: string,
    public readonly stayName: string,
    public readonly checkIn: string,
    public readonly checkOut: string,
    public readonly guests: number,
    public readonly phone: string,
    public readonly status: string,
    public readonly canCancel: boolean,
    public readonly displayTotal: string,
    public readonly displayDeposit: string,
    public readonly couponCode: string,
    public readonly message: string,
    public readonly detailUrl: string,
    public readonly editUrl: string,
    public readonly cancelUrl: string,
    public readonly airbnbUrl: string,
    public readonly createdAt: string,
  ) {}
}

export class AccountInvoice {
  constructor(
    public readonly id: number,
    public readonly title: string,
    public readonly status: string,
    public readonly displayTotal: string,
    public readonly printUrl: string,
    public readonly createdAt: string,
  ) {}
}

export class AccountSnapshot {
  constructor(
    public readonly name: string,
    public readonly email: string,
    public readonly reservations: AccountReservation[],
    public readonly invoices: AccountInvoice[],
    public readonly generatedAt: string,
  ) {}
}
