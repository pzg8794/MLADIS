export type TrendDirection = 'up' | 'down' | 'neutral';
import type { OpsReservation } from './reservations';

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
    public readonly adminUrl: string,
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
    public readonly detailUrl: string,
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

export class ReservationPricingQuote {
  constructor(
    public readonly guests: number,
    public readonly nights: number,
    public readonly nightlyCents: number,
    public readonly subtotalCents: number,
    public readonly displayNightly: string,
    public readonly displaySubtotal: string,
    public readonly extraGuestCount: number,
  ) {}
}

export class ReservationPricingPolicy {
  constructor(
    public readonly basePriceCents: number,
    public readonly includedGuests: number,
    public readonly extraGuestCents: number,
    public readonly maxGuests: number,
    public readonly currency: string,
    public readonly label: string,
    public readonly displayBasePrice: string,
    public readonly displayExtraGuestPrice: string,
  ) {}

  quote(guestsValue: string | number, nightsValue: string | number): ReservationPricingQuote {
    const guests = Math.max(Number(guestsValue) || 1, 1);
    const nights = Math.max(Number(nightsValue) || 1, 1);
    const extraGuestCount = Math.max(guests - this.includedGuests, 0);
    const nightlyCents = this.basePriceCents + (extraGuestCount * this.extraGuestCents);
    const subtotalCents = nightlyCents * nights;
    return new ReservationPricingQuote(
      guests,
      nights,
      nightlyCents,
      subtotalCents,
      this.formatMoney(nightlyCents),
      this.formatMoney(subtotalCents),
      extraGuestCount,
    );
  }

  extraGuestRuleLabel(): string {
    if (this.extraGuestCents <= 0 || this.maxGuests <= this.includedGuests) {
      return `Included up to ${this.includedGuests} guest${this.includedGuests === 1 ? '' : 's'}, max ${this.maxGuests} guests.`;
    }
    const amount = this.extraGuestCents % 100 === 0
      ? `$${this.extraGuestCents / 100}`
      : this.formatMoney(this.extraGuestCents);
    const threshold = this.includedGuests > 1 ? ` after ${this.includedGuests}` : '';
    return `${amount}/night per added guest${threshold}, max ${this.maxGuests} guests.`;
  }

  private formatMoney(cents: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency.toUpperCase(),
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(cents / 100);
  }
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
    public readonly pricing: ReservationPricingPolicy,
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

export class AgentAccessStatus {
  constructor(
    public readonly isAuthenticated: boolean,
    public readonly questionLimit: number,
    public readonly questionsUsed: number,
    public readonly remainingQuestions: number | null,
    public readonly canAsk: boolean,
    public readonly loginUrl: string,
    public readonly agentKey: string = 'public-booking-agent',
    public readonly agentName: string = 'Booking agent',
  ) {}

  asAnonymous(): AgentAccessStatus {
    return new AgentAccessStatus(
      false,
      this.questionLimit,
      0,
      this.questionLimit > 0 ? this.questionLimit : null,
      false,
      this.loginUrl,
      this.agentKey,
      this.agentName,
    );
  }
}

export type PublicUserStatus = 'checking' | 'anonymous' | 'authenticated';

export class PublicUserContext {
  constructor(
    public readonly status: PublicUserStatus,
    public readonly displayName: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly isStaff: boolean,
    public readonly agent: AgentAccessStatus,
  ) {}

  get isAuthenticated(): boolean {
    return this.status === 'authenticated';
  }

  static checking(agent: AgentAccessStatus): PublicUserContext {
    return new PublicUserContext('checking', '', '', '', false, agent.asAnonymous());
  }

  static anonymous(agent: AgentAccessStatus): PublicUserContext {
    return new PublicUserContext('anonymous', '', '', '', false, agent.asAnonymous());
  }
}

export type ReservationRequestField =
  | 'item'
  | 'guest_name'
  | 'email'
  | 'phone'
  | 'check_in'
  | 'check_out'
  | 'guests'
  | 'coupon_code'
  | 'message';

export class ReservationRequestDraft {
  constructor(
    public readonly item: string,
    public readonly guestName: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly checkIn: string,
    public readonly checkOut: string,
    public readonly guests: string,
    public readonly couponCode: string,
    public readonly message: string,
  ) {}

  static forStay(stayId?: number | null): ReservationRequestDraft {
    return new ReservationRequestDraft(stayId ? String(stayId) : '', '', '', '', '', '', '1', '', '');
  }

  withAccount(user: PublicUserContext): ReservationRequestDraft {
    return new ReservationRequestDraft(
      this.item,
      this.guestName || user.displayName,
      this.email || user.email,
      this.phone || user.phone,
      this.checkIn,
      this.checkOut,
      this.guests,
      this.couponCode,
      this.message,
    );
  }

  withField(field: ReservationRequestField, value: string): ReservationRequestDraft {
    const values = {
      item: this.item,
      guest_name: this.guestName,
      email: this.email,
      phone: this.phone,
      check_in: this.checkIn,
      check_out: this.checkOut,
      guests: this.guests,
      coupon_code: this.couponCode,
      message: this.message,
      [field]: value,
    };
    return new ReservationRequestDraft(
      values.item,
      values.guest_name,
      values.email,
      values.phone,
      values.check_in,
      values.check_out,
      values.guests,
      values.coupon_code,
      values.message,
    );
  }

  withStayPricing(policy: ReservationPricingPolicy | null): ReservationRequestDraft {
    if (!policy) return this;
    const currentGuests = Math.max(Number(this.guests) || 1, 1);
    let nextGuests = currentGuests;
    if (policy.includedGuests > 1 && currentGuests <= 1) {
      nextGuests = policy.includedGuests;
    }
    if (nextGuests > policy.maxGuests) {
      nextGuests = policy.maxGuests;
    }
    return this.withField('guests', String(nextGuests));
  }

  toFormData(csrfTokenValue: string): FormData {
    const formData = new FormData();
    formData.set('csrfmiddlewaretoken', csrfTokenValue);
    formData.set('item', this.item);
    formData.set('guest_name', this.guestName);
    formData.set('email', this.email);
    formData.set('phone', this.phone);
    formData.set('check_in', this.checkIn);
    formData.set('check_out', this.checkOut);
    formData.set('guests', this.guests || '1');
    formData.set('coupon_code', this.couponCode);
    formData.set('message', this.message);
    return formData;
  }
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
    public readonly agent: AgentAccessStatus,
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
    public readonly displaySubtotal: string,
    public readonly displayDiscount: string,
    public readonly displayReservationPayment: string,
    public readonly displayTotal: string,
    public readonly displayDeposit: string,
    public readonly reservationPaymentCents: number,
    public readonly pricing: ReservationPricingPolicy,
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
    public readonly segmentValue: string,
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
    public readonly reservations: OpsReservation[] = [],
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

export class OpsAdminRoleOption {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly count: number,
  ) {}
}

export class OpsAdminUserRow {
  constructor(
    public readonly id: number,
    public readonly name: string,
    public readonly username: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly role: string,
    public readonly roleValue: string,
    public readonly status: string,
    public readonly statusValue: string,
    public readonly accessStatus: string,
    public readonly accessStatusValue: string,
    public readonly isStaff: boolean,
    public readonly isSuperuser: boolean,
    public readonly lastLogin: string,
    public readonly joined: string,
    public readonly notes: string,
    public readonly adminUrl: string,
    public readonly accessAdminUrl: string,
  ) {}
}

export class OpsAdminSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly roleOptions: OpsAdminRoleOption[],
    public readonly rows: OpsAdminUserRow[],
    public readonly adminUrl: string,
    public readonly accessAdminUrl: string,
    public readonly generatedAt: string,
  ) {}
}

export class OpsSettingsField {
  constructor(
    public readonly key: string,
    public readonly label: string,
    public readonly value: string | boolean | number,
    public readonly type: string,
  ) {}
}

export class OpsSettingsSection {
  constructor(
    public readonly id: string,
    public readonly label: string,
    public readonly status: string,
    public readonly statusTone: string,
    public readonly description: string,
    public readonly fields: OpsSettingsField[],
  ) {}
}

export class OpsSettingsSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly sections: OpsSettingsSection[],
    public readonly adminUrls: Record<string, string>,
    public readonly generatedAt: string,
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

export type OpsCalendarViewMode = 'week' | 'month' | 'list';
export type OpsCalendarEventType = 'reservation' | 'block' | 'price';

export class OpsCalendarStay {
  constructor(
    public readonly id: number,
    public readonly name: string,
    public readonly slug: string,
    public readonly subtitle: string,
    public readonly defaultPrice: string,
    public readonly isConfigured: boolean,
    public readonly feedLabel: string,
    public readonly feedStatus: string,
    public readonly lastCheckedAt: string,
  ) {}
}

export class OpsCalendarDay {
  constructor(
    public readonly date: string,
    public readonly day: number,
    public readonly weekday: string,
    public readonly label: string,
    public readonly inMonth: boolean,
    public readonly isToday: boolean,
    public readonly status: string,
    public readonly reservationCount: number,
    public readonly blockCount: number,
    public readonly hasPriceOverride: boolean,
    public readonly priceDisplay: string,
    public readonly priceSource: string,
    public readonly priceLabel: string,
  ) {}
}

export class OpsCalendarEvent {
  constructor(
    public readonly id: string,
    public readonly recordId: number,
    public readonly type: OpsCalendarEventType,
    public readonly title: string,
    public readonly subtitle: string,
    public readonly itemId: number,
    public readonly itemName: string,
    public readonly start: string,
    public readonly end: string,
    public readonly rangeLabel: string,
    public readonly status: string,
    public readonly guestLabel: string,
    public readonly amount: string,
    public readonly adminUrl: string,
  ) {}
}

export class OpsCalendarStayRow {
  constructor(
    public readonly stay: OpsCalendarStay,
    public readonly weekDays: OpsCalendarDay[],
    public readonly weeks: OpsCalendarDay[][],
    public readonly events: OpsCalendarEvent[],
  ) {}
}

export class OpsCalendarSnapshot {
  constructor(
    public readonly view: OpsCalendarViewMode,
    public readonly focusDate: string,
    public readonly monthLabel: string,
    public readonly visibleStart: string,
    public readonly visibleEnd: string,
    public readonly previousDate: string,
    public readonly nextDate: string,
    public readonly selectedItemId: number | null,
    public readonly stays: OpsCalendarStay[],
    public readonly summaryCards: OpsMetric[],
    public readonly weeks: OpsCalendarDay[][],
    public readonly weekDays: OpsCalendarDay[],
    public readonly stayRows: OpsCalendarStayRow[],
    public readonly events: OpsCalendarEvent[],
    public readonly agenda: OpsCalendarEvent[],
    public readonly adminRecordsUrl: string,
    public readonly generatedAt: string,
  ) {}
}

export class OpsMaintenanceOption {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly count: number,
  ) {}
}

export class OpsMaintenanceStay {
  constructor(
    public readonly id: number,
    public readonly name: string,
    public readonly slug: string,
    public readonly subtitle: string,
    public readonly maxGuests: number,
  ) {}
}

export class OpsMaintenanceReservation {
  constructor(
    public readonly id: number,
    public readonly requestKey: string,
    public readonly label: string,
    public readonly guestName: string,
    public readonly itemId: number | null,
    public readonly itemName: string,
    public readonly checkIn: string,
    public readonly checkOut: string,
    public readonly dateRange: string,
    public readonly guests: number,
    public readonly status: string,
    public readonly statusLabel: string,
    public readonly displayTotal: string,
    public readonly adminUrl: string,
  ) {}
}

export class OpsMaintenancePhoto {
  constructor(
    public readonly id: string,
    public readonly url: string,
    public readonly caption: string,
    public readonly sortOrder: number,
    public readonly isCover: boolean,
    public readonly mimeType: string,
    public readonly fileSizeBytes: number,
    public readonly checksumSha256: string,
    public readonly uploadedAt: string,
  ) {}
}

export class OpsMaintenanceEvent {
  constructor(
    public readonly id: string,
    public readonly title: string,
    public readonly itemId: number,
    public readonly itemName: string,
    public readonly bookingId: number | null,
    public readonly bookingRequestKey: string,
    public readonly bookingLabel: string,
    public readonly bookingGuestName: string,
    public readonly bookingDateRange: string,
    public readonly bookingAdminUrl: string,
    public readonly workType: string,
    public readonly workTypeLabel: string,
    public readonly status: string,
    public readonly statusLabel: string,
    public readonly paymentStatus: string,
    public readonly paymentStatusLabel: string,
    public readonly displayCost: string,
    public readonly costAmount: string,
    public readonly costCurrency: string,
    public readonly reportedAt: string,
    public readonly reportedLabel: string,
    public readonly startedAt: string,
    public readonly completedAt: string,
    public readonly durationMinutes: number | null,
    public readonly vendorName: string,
    public readonly vendorContact: string,
    public readonly invoiceNumber: string,
    public readonly proofOfPaymentRef: string,
    public readonly taxCategoryCode: string,
    public readonly description: string,
    public readonly aiDescription: string,
    public readonly aiDescriptionGeneratedAt: string,
    public readonly aiDescriptionModel: string,
    public readonly aiDescriptionMetadata: Record<string, unknown>,
    public readonly useAiDescription: boolean,
    public readonly adminNotes: string,
    public readonly photoCount: number,
    public readonly firstPhotoUrl: string,
    public readonly isTaxReady: boolean,
    public readonly createdBy: string,
    public readonly adminUrl: string,
    public readonly agentPayloadUrl: string,
    public readonly aiDescriptionUrl: string,
    public readonly photos: OpsMaintenancePhoto[],
    public readonly createdAt: string,
    public readonly updatedAt: string,
  ) {}
}

export class OpsMaintenanceSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly workTypeOptions: OpsMaintenanceOption[],
    public readonly statusOptions: OpsMaintenanceOption[],
    public readonly paymentStatusOptions: OpsMaintenanceOption[],
    public readonly stays: OpsMaintenanceStay[],
    public readonly reservations: OpsMaintenanceReservation[],
    public readonly rows: OpsMaintenanceEvent[],
    public readonly adminUrl: string,
    public readonly addAdminUrl: string,
    public readonly generatedAt: string,
  ) {}
}

export class OpsWorkItem {
  constructor(
    public readonly id: number,
    public readonly title: string,
    public readonly description: string,
    public readonly listName: string,
    public readonly neuron: string,
    public readonly neuronLabel: string,
    public readonly status: string,
    public readonly statusLabel: string,
    public readonly priority: string,
    public readonly priorityLabel: string,
    public readonly nextAction: string,
    public readonly sourceUrl: string,
    public readonly githubUrl: string,
    public readonly driveUrl: string,
    public readonly dueDate: string,
    public readonly completedAt: string,
    public readonly updatedAt: string,
    public readonly isDone: boolean,
  ) {}
}

export class OpsWorkItemList {
  constructor(
    public readonly name: string,
    public readonly total: number,
    public readonly done: number,
    public readonly open: number,
    public readonly items: OpsWorkItem[],
  ) {}
}

export class OpsWorkStatusColumn {
  constructor(
    public readonly status: string,
    public readonly label: string,
    public readonly items: OpsWorkItem[],
  ) {}
}

export class OpsWorkboardSnapshot {
  constructor(
    public readonly summaryCards: OpsMetric[],
    public readonly lists: OpsWorkItemList[],
    public readonly statusColumns: OpsWorkStatusColumn[],
    public readonly focusItems: OpsWorkItem[],
    public readonly generatedAt: string,
  ) {}
}
