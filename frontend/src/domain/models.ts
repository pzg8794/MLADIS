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

export class SocialLoginProvider {
  constructor(
    public readonly id: string,
    public readonly label: string,
    public readonly loginUrl: string,
    public readonly isConfigured: boolean,
    public readonly isLaunchable: boolean,
    public readonly disabledReason: string,
    public readonly helpText: string,
  ) {}
}

export type PublicChatKitMode = 'managed' | 'custom';

export class PublicChatKitConfig {
  constructor(
    public readonly mode: PublicChatKitMode,
    public readonly sessionUrl: string | null,
    public readonly apiUrl: string | null,
    public readonly domainKey: string | null,
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
    public readonly socialProviders: SocialLoginProvider[],
    public readonly chatKit: PublicChatKitConfig | null,
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
    public readonly isStaff: boolean,
    public readonly isSuperuser: boolean,
    public readonly reservations: AccountReservation[],
    public readonly invoices: AccountInvoice[],
    public readonly generatedAt: string,
  ) {}
}

export class OpsReservationMetric {
  constructor(
    public readonly label: string,
    public readonly value: number,
    public readonly caption: string,
  ) {}
}

export class OpsReservationSegment {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly count: number,
    public readonly url: string,
  ) {}
}

export class OpsReservationRow {
  constructor(
    public readonly id: number,
    public readonly recordType: 'direct' | 'airbnb',
    public readonly name: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly contactPath: string,
    public readonly listing: string,
    public readonly listingId: string,
    public readonly stayDates: string,
    public readonly guests: string,
    public readonly rating: string,
    public readonly feedback: string,
    public readonly sourceSubject: string,
    public readonly threadUrl: string,
    public readonly consentStatus: string,
    public readonly segment: string,
    public readonly recordAdminUrl: string,
    public readonly profileAdminUrl: string,
    public readonly feedbackAdminUrl: string,
    public readonly updatedAt: string,
  ) {}
}

export class OpsReservationsSnapshot {
  constructor(
    public readonly summaryCards: OpsReservationMetric[],
    public readonly segmentOptions: OpsReservationSegment[],
    public readonly selectedSegment: string,
    public readonly exportUrl: string,
    public readonly legacyUrl: string,
    public readonly rows: OpsReservationRow[],
    public readonly generatedAt: string,
  ) {}
}

export class OpsMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
  ) {}
}

export class OpsChartRow {
  constructor(
    public readonly label: string,
    public readonly total: number,
    public readonly width: number,
  ) {}
}

export class OpsChart {
  constructor(
    public readonly id: string,
    public readonly title: string,
    public readonly category: string,
    public readonly rows: OpsChartRow[],
    public readonly maxTotal: number,
  ) {}
}

export class OpsReportsSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly charts: OpsChart[],
    public readonly reportSince: string,
    public readonly reportUntil: string,
    public readonly legacyUrl: string,
    public readonly calendarUrl: string,
  ) {}
}

export class OpsSegmentOption {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly count: number,
    public readonly url: string,
  ) {}
}

export class OpsCustomerRow {
  constructor(
    public readonly id: number,
    public readonly name: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly segment: string,
    public readonly segmentValue: string,
    public readonly source: string,
    public readonly marketingConsent: string,
    public readonly canReceivePromotions: boolean,
    public readonly directReservations: number,
    public readonly airbnbReservations: number,
    public readonly feedbackCount: number,
    public readonly invoiceCount: number,
    public readonly lastStay: string,
    public readonly notes: string,
    public readonly adminUrl: string,
    public readonly updatedAt: string,
  ) {}
}

export class OpsCustomersSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly segmentOptions: OpsSegmentOption[],
    public readonly rows: OpsCustomerRow[],
    public readonly adminUrl: string,
    public readonly legacyUrl: string,
    public readonly generatedAt: string,
  ) {}
}

export class OpsDepositStatusOption {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly count: number,
  ) {}
}

export class OpsDepositRow {
  constructor(
    public readonly id: number,
    public readonly guestName: string,
    public readonly email: string,
    public readonly stayName: string,
    public readonly amount: string,
    public readonly provider: string,
    public readonly status: string,
    public readonly statusLabel: string,
    public readonly checkoutUrl: string,
    public readonly notes: string,
    public readonly adminUrl: string,
    public readonly inquiryAdminUrl: string,
    public readonly createdLabel: string,
    public readonly updatedAt: string,
  ) {}
}

export class OpsDepositsSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly statusOptions: OpsDepositStatusOption[],
    public readonly rows: OpsDepositRow[],
    public readonly adminUrl: string,
    public readonly generatedAt: string,
  ) {}
}

export class OpsAgentTopic {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly total: number,
    public readonly width: number,
  ) {}
}

export class OpsAgentConversation {
  constructor(
    public readonly id: number,
    public readonly topic: string,
    public readonly mode: string,
    public readonly item: string,
    public readonly visitor: string,
    public readonly lastQuestion: string,
    public readonly lastReply: string,
    public readonly language: string,
    public readonly adminUrl: string,
    public readonly updatedAt: string,
  ) {}
}

export class OpsAgentFaq {
  constructor(
    public readonly id: number,
    public readonly question: string,
    public readonly answer: string,
    public readonly category: string,
    public readonly keywords: string,
    public readonly item: string,
    public readonly language: string,
    public readonly minScore: string,
    public readonly priority: number,
    public readonly isActive: boolean,
    public readonly adminUrl: string,
    public readonly updatedAt: string,
  ) {}
}

export class OpsAgentSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly topics: OpsAgentTopic[],
    public readonly conversations: OpsAgentConversation[],
    public readonly faqs: OpsAgentFaq[],
    public readonly faqAdminUrl: string,
    public readonly conversationAdminUrl: string,
    public readonly generatedAt: string,
  ) {}
}
