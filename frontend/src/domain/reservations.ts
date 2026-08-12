export type ReservationStatusFilter = 'all' | 'confirmed' | 'pending' | 'hold' | 'cancelled' | 'completed';
export type ReservationRecordType = 'direct' | 'airbnb';
export type ReservationRiskLevel = 'low' | 'medium' | 'high';
export type ReservationDepositTone = 'paid' | 'hold' | 'pending' | 'none' | 'unpaid';
export type ReservationDetailTab = 'messages' | 'payments' | 'deposits' | 'documents' | 'activity';

export interface ReservationMoneyPayload {
  amount_cents: number;
  currency: string;
  display: string;
}

export interface ReservationGuestPayload {
  name: string;
  email: string;
  phone: string;
  contact_label: string;
  country: string;
  profile_admin_url: string;
  thread_url: string;
  segment: string;
  segment_value: string;
}

export interface ReservationStayPayload {
  id: number | string;
  name: string;
  unit_label: string;
  listing_id: string;
  admin_url: string;
}

export interface ReservationDatesPayload {
  check_in: string;
  check_out: string;
  nights: number;
  display_range: string;
  nights_label: string;
}

export interface ReservationStatusPayload {
  value: string;
  label: string;
  tone: string;
  tab: ReservationStatusFilter;
}

export interface ReservationRiskPayload {
  level: ReservationRiskLevel;
  label: string;
  signals: string[];
}

export interface ReservationPaymentStepPayload {
  label: string;
  amount: ReservationMoneyPayload;
  status: string;
  due_label: string;
}

export interface ReservationPaymentPlanPayload {
  total: ReservationMoneyPayload;
  stay_payment: ReservationMoneyPayload;
  deposit: ReservationMoneyPayload;
  status: string;
  steps: ReservationPaymentStepPayload[];
}

export interface ReservationDepositHoldPayload {
  amount: ReservationMoneyPayload;
  status: string;
  label: string;
  expires_at: string;
  provider: string;
  can_approve: boolean;
  can_release: boolean;
}

export interface ReservationDocumentPayload {
  property_rules_accepted: boolean;
  damage_terms_accepted: boolean;
  property_rules_version: string;
  damage_terms_version: string;
  all_accepted: boolean;
}

export interface ReservationMessagePayload {
  id: string;
  sender_label: string;
  body: string;
  status: string;
  timestamp: string;
  from_staff: boolean;
}

export interface ReservationMessagesPayload {
  suggested_draft: string;
  items: ReservationMessagePayload[];
}

export interface ReservationTimelinePayload {
  type: string;
  label: string;
  actor: string;
  timestamp: string;
  note: string;
}

export interface ReservationAgentPayload {
  risk_level: ReservationRiskLevel;
  suggested_reply: string;
  missing_information: string[];
  recommended_actions: string[];
  positive_signals: string[];
}

export interface ReservationAdminPayload {
  record_url: string;
  profile_url: string;
  feedback_url: string;
  can_transition_status: boolean;
}

export interface LegacyReservationRowPayload {
  id: number;
  record_type: ReservationRecordType;
  name: string;
  email: string;
  phone: string;
  contact_path: string;
  listing: string;
  listing_id: string;
  stay_dates: string;
  guests: string;
  rating: string;
  feedback: string;
  source_subject: string;
  thread_url: string;
  consent_status: string;
  segment: string;
  segment_value: string;
  record_admin_url: string;
  profile_admin_url: string;
  feedback_admin_url: string;
  updated_at: string;
}

export interface OpsReservationPayload {
  id: string;
  key: string;
  record_type: ReservationRecordType;
  request_key: string;
  guest: ReservationGuestPayload;
  stay: ReservationStayPayload;
  dates: ReservationDatesPayload;
  status: ReservationStatusPayload;
  risk: ReservationRiskPayload;
  payment_plan: ReservationPaymentPlanPayload;
  deposit_hold: ReservationDepositHoldPayload;
  documents: ReservationDocumentPayload;
  messages: ReservationMessagesPayload;
  timeline: ReservationTimelinePayload[];
  agent: ReservationAgentPayload;
  admin: ReservationAdminPayload;
  legacy_row: LegacyReservationRowPayload;
}

export class ReservationMoney {
  constructor(
    public readonly cents: number,
    public readonly currency: string,
    public readonly display: string,
  ) {}

  static fromPayload(payload: ReservationMoneyPayload): ReservationMoney {
    return new ReservationMoney(payload.amount_cents, payload.currency, payload.display);
  }

  withCurrencySuffix(): string {
    return `${this.display} ${this.currency}`;
  }
}

export class ReservationGuest {
  constructor(
    public readonly name: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly contactLabel: string,
    public readonly country: string,
    public readonly profileAdminUrl: string,
    public readonly threadUrl: string,
    public readonly segment: string,
    public readonly segmentValue: string,
  ) {}

  static fromPayload(payload: ReservationGuestPayload): ReservationGuest {
    return new ReservationGuest(
      payload.name,
      payload.email,
      payload.phone,
      payload.contact_label,
      payload.country,
      payload.profile_admin_url,
      payload.thread_url,
      payload.segment,
      payload.segment_value,
    );
  }

  get initials(): string {
    const parts = this.name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'G';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
}

export class ReservationStay {
  constructor(
    public readonly id: number | string,
    public readonly name: string,
    public readonly unitLabel: string,
    public readonly listingId: string,
    public readonly adminUrl: string,
  ) {}

  static fromPayload(payload: ReservationStayPayload): ReservationStay {
    return new ReservationStay(
      payload.id,
      normalizeStayName(payload.name || 'Flexible stay'),
      payload.unit_label,
      payload.listing_id,
      payload.admin_url,
    );
  }

  get displayId(): string {
    return String(this.listingId || this.id || 'pending');
  }
}

export class ReservationDates {
  constructor(
    public readonly checkIn: string,
    public readonly checkOut: string,
    public readonly nights: number,
    public readonly displayRange: string,
    public readonly nightsLabel: string,
  ) {}

  static fromPayload(payload: ReservationDatesPayload): ReservationDates {
    return new ReservationDates(
      payload.check_in,
      payload.check_out,
      payload.nights,
      payload.display_range || 'Dates pending',
      payload.nights_label || 'Dates pending',
    );
  }
}

export class ReservationStatusState {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly tone: string,
    public readonly tab: ReservationStatusFilter,
  ) {}

  static fromPayload(payload: ReservationStatusPayload): ReservationStatusState {
    return new ReservationStatusState(payload.value, payload.label, payload.tone, payload.tab);
  }
}

export class ReservationRiskState {
  constructor(
    public readonly level: ReservationRiskLevel,
    public readonly label: string,
    public readonly signals: string[],
  ) {}

  static fromPayload(payload: ReservationRiskPayload): ReservationRiskState {
    return new ReservationRiskState(payload.level, payload.label, payload.signals);
  }
}

export class ReservationPaymentStep {
  constructor(
    public readonly label: string,
    public readonly amount: ReservationMoney,
    public readonly status: string,
    public readonly dueLabel: string,
  ) {}

  static fromPayload(payload: ReservationPaymentStepPayload): ReservationPaymentStep {
    return new ReservationPaymentStep(
      payload.label,
      ReservationMoney.fromPayload(payload.amount),
      payload.status,
      payload.due_label,
    );
  }
}

export class ReservationPaymentPlan {
  constructor(
    public readonly total: ReservationMoney,
    public readonly stayPayment: ReservationMoney,
    public readonly deposit: ReservationMoney,
    public readonly status: string,
    public readonly steps: ReservationPaymentStep[],
  ) {}

  static fromPayload(payload: ReservationPaymentPlanPayload): ReservationPaymentPlan {
    return new ReservationPaymentPlan(
      ReservationMoney.fromPayload(payload.total),
      ReservationMoney.fromPayload(payload.stay_payment),
      ReservationMoney.fromPayload(payload.deposit),
      payload.status,
      payload.steps.map(ReservationPaymentStep.fromPayload),
    );
  }

  get tone(): ReservationDepositTone {
    if (this.status === 'paid') return 'paid';
    if (this.status === 'pending') return 'pending';
    if (this.status === 'cancelled' || this.status === 'canceled') return 'none';
    return 'unpaid';
  }

  get label(): string {
    if (this.status === 'paid') return 'Paid';
    if (this.status === 'pending') return 'Pending';
    if (this.status === 'imported') return 'Imported';
    if (this.status === 'cancelled' || this.status === 'canceled') return 'N/A';
    return 'Unpaid';
  }
}

export class ReservationDepositHold {
  constructor(
    public readonly amount: ReservationMoney,
    public readonly status: string,
    public readonly label: string,
    public readonly expiresAt: string,
    public readonly provider: string,
    public readonly canApprove: boolean,
    public readonly canRelease: boolean,
  ) {}

  static fromPayload(payload: ReservationDepositHoldPayload): ReservationDepositHold {
    return new ReservationDepositHold(
      ReservationMoney.fromPayload(payload.amount),
      payload.status,
      payload.label,
      payload.expires_at,
      payload.provider,
      payload.can_approve,
      payload.can_release,
    );
  }

  get tone(): ReservationDepositTone {
    if (this.status === 'none') return 'none';
    if (this.status === 'captured') return 'paid';
    if (this.status === 'requires_capture' || this.label.toLowerCase().includes('hold')) return 'hold';
    if (this.status === 'canceled' || this.status === 'cancelled') return 'none';
    return 'pending';
  }
}

export class ReservationDocuments {
  constructor(
    public readonly propertyRulesAccepted: boolean,
    public readonly damageTermsAccepted: boolean,
    public readonly propertyRulesVersion: string,
    public readonly damageTermsVersion: string,
    public readonly allAccepted: boolean,
  ) {}

  static fromPayload(payload: ReservationDocumentPayload): ReservationDocuments {
    return new ReservationDocuments(
      payload.property_rules_accepted,
      payload.damage_terms_accepted,
      payload.property_rules_version,
      payload.damage_terms_version,
      payload.all_accepted,
    );
  }
}

export class ReservationMessage {
  constructor(
    public readonly id: string,
    public readonly senderLabel: string,
    public readonly body: string,
    public readonly status: string,
    public readonly timestamp: string,
    public readonly fromStaff: boolean,
  ) {}

  static fromPayload(payload: ReservationMessagePayload): ReservationMessage {
    return new ReservationMessage(
      payload.id,
      payload.sender_label,
      payload.body,
      payload.status,
      payload.timestamp,
      payload.from_staff,
    );
  }
}

export class ReservationMessageThread {
  constructor(
    public readonly suggestedDraft: string,
    public readonly items: ReservationMessage[],
  ) {}

  static fromPayload(payload: ReservationMessagesPayload): ReservationMessageThread {
    return new ReservationMessageThread(
      payload.suggested_draft,
      payload.items.map(ReservationMessage.fromPayload),
    );
  }
}

export class ReservationTimelineEvent {
  constructor(
    public readonly type: string,
    public readonly label: string,
    public readonly actor: string,
    public readonly timestamp: string,
    public readonly note: string,
  ) {}

  static fromPayload(payload: ReservationTimelinePayload): ReservationTimelineEvent {
    return new ReservationTimelineEvent(
      payload.type,
      payload.label,
      payload.actor,
      payload.timestamp,
      payload.note,
    );
  }
}

export class ReservationAgentAssessment {
  constructor(
    public readonly riskLevel: ReservationRiskLevel,
    public readonly suggestedReply: string,
    public readonly missingInformation: string[],
    public readonly recommendedActions: string[],
    public readonly positiveSignals: string[],
  ) {}

  static fromPayload(payload: ReservationAgentPayload): ReservationAgentAssessment {
    return new ReservationAgentAssessment(
      payload.risk_level,
      payload.suggested_reply,
      payload.missing_information,
      payload.recommended_actions,
      payload.positive_signals,
    );
  }
}

export class OpsReservation {
  constructor(
    public readonly id: string,
    public readonly key: string,
    public readonly recordType: ReservationRecordType,
    public readonly requestKey: string,
    public readonly guest: ReservationGuest,
    public readonly stay: ReservationStay,
    public readonly dates: ReservationDates,
    public readonly status: ReservationStatusState,
    public readonly risk: ReservationRiskState,
    public readonly paymentPlan: ReservationPaymentPlan,
    public readonly depositHold: ReservationDepositHold,
    public readonly documents: ReservationDocuments,
    public readonly messages: ReservationMessageThread,
    public readonly timeline: ReservationTimelineEvent[],
    public readonly agent: ReservationAgentAssessment,
    public readonly admin: ReservationAdminPayload,
    public readonly legacyRow: LegacyReservationRowPayload,
  ) {}

  static fromPayload(payload: OpsReservationPayload): OpsReservation {
    return new OpsReservation(
      payload.id,
      payload.key,
      payload.record_type,
      payload.request_key,
      ReservationGuest.fromPayload(payload.guest),
      ReservationStay.fromPayload(payload.stay),
      ReservationDates.fromPayload(payload.dates),
      ReservationStatusState.fromPayload(payload.status),
      ReservationRiskState.fromPayload(payload.risk),
      ReservationPaymentPlan.fromPayload(payload.payment_plan),
      ReservationDepositHold.fromPayload(payload.deposit_hold),
      ReservationDocuments.fromPayload(payload.documents),
      ReservationMessageThread.fromPayload(payload.messages),
      payload.timeline.map(ReservationTimelineEvent.fromPayload),
      ReservationAgentAssessment.fromPayload(payload.agent),
      payload.admin,
      payload.legacy_row,
    );
  }

  get initials(): string {
    return this.guest.initials;
  }

  get statusFilter(): ReservationStatusFilter {
    return this.status.tab;
  }

  get listing(): string {
    return this.stay.name;
  }

  get guestsLabel(): string {
    return String(this.legacyRow.guests || '1');
  }

  get searchText(): string {
    return [
      this.requestKey,
      this.guest.name,
      this.guest.email,
      this.guest.phone,
      this.guest.contactLabel,
      this.stay.name,
      this.stay.listingId,
      this.dates.displayRange,
      this.legacyRow.feedback,
      this.legacyRow.source_subject,
      this.channel,
      this.guest.country,
      this.risk.label,
    ].join(' ').toLowerCase();
  }

  get channel(): string {
    return this.recordType === 'airbnb' ? 'Airbnb' : 'Direct Website';
  }

  canTransitionStatus(): boolean {
    return this.admin.can_transition_status;
  }

  matchesSearch(query: string): boolean {
    const normalized = query.trim().toLowerCase();
    return !normalized || this.searchText.includes(normalized);
  }

  matchesStatus(status: ReservationStatusFilter): boolean {
    return status === 'all' || this.statusFilter === status;
  }
}

export interface ReservationWorkspaceFilters {
  search: string;
  status: ReservationStatusFilter;
  listing: string;
  channel: string;
  country: string;
  risk: string;
}

export function reservationStatusCounts(reservations: OpsReservation[]): Record<ReservationStatusFilter, number> {
  return reservations.reduce<Record<ReservationStatusFilter, number>>(
    (counts, reservation) => {
      counts.all += 1;
      counts[reservation.statusFilter] += 1;
      return counts;
    },
    { all: 0, confirmed: 0, pending: 0, hold: 0, cancelled: 0, completed: 0 },
  );
}

export function filterReservations(reservations: OpsReservation[], filters: ReservationWorkspaceFilters): OpsReservation[] {
  return reservations.filter((reservation) => {
    const listingMatch = filters.listing === 'All listings' || reservation.listing === filters.listing;
    const channelMatch = filters.channel === 'All channels' || reservation.channel === filters.channel;
    const countryMatch = filters.country === 'All countries' || reservation.guest.country === filters.country;
    const riskMatch = filters.risk === 'All levels' || reservation.risk.label === filters.risk;
    return (
      reservation.matchesSearch(filters.search)
      && reservation.matchesStatus(filters.status)
      && listingMatch
      && channelMatch
      && countryMatch
      && riskMatch
    );
  });
}

export function reservationOptions(reservations: OpsReservation[]) {
  return {
    listings: ['All listings', ...Array.from(new Set(reservations.map((reservation) => reservation.listing))).slice(0, 8)],
    channels: ['All channels', ...Array.from(new Set(reservations.map((reservation) => reservation.channel)))],
    countries: ['All countries', ...Array.from(new Set(reservations.map((reservation) => reservation.guest.country)))],
  };
}

function normalizeStayName(value: string) {
  const clean = value
    .replace(/^MLADIS\s*[-–]\s*/i, '')
    .replace(/\bBedrooms?\b/gi, 'Beds')
    .replace(/\s+/g, ' ')
    .trim();
  const formattedMatch = clean.match(/^(\d+)\s+Beds?\s+Apts?,?\s+(.+)$/i);
  if (formattedMatch) {
    const bedrooms = formattedMatch[1];
    const title = formattedMatch[2].replace(/,?\s+G-\d+$/i, '').replace(/,+$/g, '').trim();
    const block = clean.match(/\bG-\d+\b/i)?.[0] || '';
    return [`${bedrooms} Beds Apt`, title, block].filter(Boolean).join(', ');
  }

  const match = clean.match(/^(\d+)\s+Beds?\s+(.+?)(?:\s+(G-\d+))?$/i);
  if (!match) return clean;

  const bedrooms = match[1];
  const title = match[2].replace(/\s+G-\d+$/i, '').replace(/,+$/g, '').trim();
  const block = match[3] || clean.match(/\bG-\d+\b/i)?.[0] || '';
  return [`${bedrooms} Beds Apt`, title, block].filter(Boolean).join(', ');
}
