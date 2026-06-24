export type DepositHoldTone = 'green' | 'orange' | 'blue' | 'red' | 'purple';
export type DepositRiskTone = 'low' | 'medium';
export type DepositStatusTone = 'on-hold' | 'approved' | 'released' | 'failed' | 'review';
export type DepositHoldAction = 'approve' | 'release' | 'request-guest-action';

export interface DepositMoneyPayload {
  amount_cents: number;
  currency: string;
  display: string;
  with_currency: string;
}

export interface DepositMetricPayload {
  label: string;
  value: string | number;
  caption?: string;
  trend?: string;
  tone?: DepositHoldTone;
  points?: string;
}

export interface DepositReservationPayload {
  id: number | null;
  key: string;
  request_key: string;
  number: string;
  listing: string;
  date_range: string;
  nights: number;
  guests: number;
  admin_url: string;
  selectable_url: string;
  image_url: string;
}

export interface DepositGuestPayload {
  id: number | null;
  name: string;
  email: string;
  phone: string;
  repeat_guest: boolean;
  view_url: string;
}

export interface DepositTimelinePayload {
  title: string;
  timestamp: string;
  note: string;
  tone: DepositHoldTone;
}

export interface DepositPaymentAttemptPayload {
  provider: string;
  brand: string;
  method: string;
  status: string;
  status_tone: DepositStatusTone;
  auth_id: string;
  amount: DepositMoneyPayload;
  timestamp: string;
  payment_url: string;
  can_open_payment: boolean;
  disabled_reason: string;
}

export interface DepositReceiptPayload {
  view_url: string;
  download_url: string;
  can_generate: boolean;
  disabled_reason: string;
}

export interface DepositHoldActionsPayload {
  can_approve: boolean;
  can_release: boolean;
  can_request_guest_action: boolean;
}

export interface DepositHoldPayload {
  id: string;
  record_id: number;
  source: string;
  kind: string;
  kind_label: string;
  hold_number: string;
  guest_name: string;
  email: string;
  initials: string;
  phone: string;
  repeat_guest: boolean;
  guest: DepositGuestPayload;
  stay_name: string;
  listing: string;
  reservation: DepositReservationPayload;
  amount: string;
  money: DepositMoneyPayload;
  amount_cents: number;
  currency: string;
  provider: string;
  status: string;
  status_label: string;
  status_tone: DepositStatusTone;
  checkout_url: string;
  notes: string;
  admin_url: string;
  inquiry_admin_url: string;
  created_at: string;
  created_label: string;
  requested: { date: string; time: string; label: string };
  expires_at: string;
  expiration: { date: string; time: string; label: string; time_left: string };
  risk: string;
  risk_tone: DepositRiskTone;
  has_warning: boolean;
  updated_at: string;
  timeline: DepositTimelinePayload[];
  payment_attempts: DepositPaymentAttemptPayload[];
  receipt: DepositReceiptPayload;
  actions: DepositHoldActionsPayload;
}

export interface ExpiringHoldPayload {
  id: string;
  guest: string;
  listing: string;
  time_left: string;
}

export interface DepositStatusOptionPayload {
  value: string;
  label: string;
  count: number;
}

export interface DepositHoldsSnapshotPayload {
  summary_cards: DepositMetricPayload[];
  status_options: DepositStatusOptionPayload[];
  rows: DepositHoldPayload[];
  expiring_holds: ExpiringHoldPayload[];
  admin_url: string;
  generated_at: string;
}

export class DepositMoney {
  constructor(
    public readonly cents: number,
    public readonly currency: string,
    public readonly display: string,
    public readonly withCurrency: string,
  ) {}

  static fromPayload(payload: DepositMoneyPayload): DepositMoney {
    return new DepositMoney(
      payload.amount_cents,
      payload.currency,
      payload.display,
      payload.with_currency,
    );
  }
}

export class DepositMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly trend: string,
    public readonly tone: DepositHoldTone,
    public readonly points: string,
  ) {}

  static fromPayload(payload: DepositMetricPayload): DepositMetric {
    return new DepositMetric(
      payload.label,
      String(payload.value),
      payload.trend || payload.caption || 'Live ledger',
      payload.tone || 'blue',
      payload.points || 'M0 38 L22 34 L44 24 L66 29 L88 26 L110 14 L132 27 L154 31 L176 37 L198 28 L220 32',
    );
  }
}

export class DepositReservation {
  private static readonly fallbackImages = [
    '/static/frontend/modern-dashboard/stays/stay-3br.jpg',
    '/static/frontend/modern-dashboard/stays/stay-2br.jpg',
    '/static/frontend/modern-dashboard/stays/stay-6br.jpg',
  ];

  constructor(
    public readonly id: number | null,
    public readonly key: string,
    public readonly requestKey: string,
    public readonly number: string,
    public readonly listing: string,
    public readonly dateRange: string,
    public readonly nights: number,
    public readonly guests: number,
    public readonly adminUrl: string,
    public readonly selectableUrl: string,
    public readonly imageUrl: string,
  ) {}

  static fromPayload(payload: DepositReservationPayload): DepositReservation {
    return new DepositReservation(
      payload.id,
      payload.key,
      payload.request_key,
      payload.number,
      payload.listing,
      payload.date_range,
      payload.nights,
      payload.guests,
      payload.admin_url,
      payload.selectable_url,
      payload.image_url,
    );
  }

  get nightsLabel(): string {
    return this.nights ? `${this.nights} nights` : 'Dates pending';
  }

  get imageFallbackUrl(): string {
    const normalized = this.listing.toLowerCase();
    if (normalized.includes('6 beds')) return DepositReservation.fallbackImages[2];
    if (normalized.includes('2 beds')) return DepositReservation.fallbackImages[1];
    return DepositReservation.fallbackImages[0];
  }

  get displayImageUrl(): string {
    return this.imageUrl || this.imageFallbackUrl;
  }
}

export class DepositGuest {
  constructor(
    public readonly id: number | null,
    public readonly name: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly repeatGuest: boolean,
    public readonly viewUrl: string,
  ) {}

  static fromPayload(payload: DepositGuestPayload): DepositGuest {
    return new DepositGuest(
      payload.id,
      payload.name,
      payload.email,
      payload.phone,
      payload.repeat_guest,
      payload.view_url,
    );
  }
}

export class DepositTimelineItem {
  constructor(
    public readonly title: string,
    public readonly timestamp: string,
    public readonly note: string,
    public readonly tone: DepositHoldTone,
  ) {}

  static fromPayload(payload: DepositTimelinePayload): DepositTimelineItem {
    return new DepositTimelineItem(payload.title, payload.timestamp, payload.note, payload.tone);
  }
}

export class DepositPaymentAttempt {
  constructor(
    public readonly provider: string,
    public readonly brand: string,
    public readonly method: string,
    public readonly status: string,
    public readonly statusTone: DepositStatusTone,
    public readonly authId: string,
    public readonly amount: DepositMoney,
    public readonly timestamp: string,
    public readonly paymentUrl: string,
    public readonly canOpenPayment: boolean,
    public readonly disabledReason: string,
  ) {}

  static fromPayload(payload: DepositPaymentAttemptPayload): DepositPaymentAttempt {
    return new DepositPaymentAttempt(
      payload.provider,
      payload.brand,
      payload.method,
      payload.status,
      payload.status_tone,
      payload.auth_id,
      DepositMoney.fromPayload(payload.amount),
      payload.timestamp,
      payload.payment_url,
      payload.can_open_payment,
      payload.disabled_reason,
    );
  }
}

export class DepositReceipt {
  constructor(
    public readonly viewUrl: string,
    public readonly downloadUrl: string,
    public readonly canGenerate: boolean,
    public readonly disabledReason: string,
  ) {}

  static fromPayload(payload: DepositReceiptPayload): DepositReceipt {
    return new DepositReceipt(
      payload.view_url,
      payload.download_url,
      payload.can_generate,
      payload.disabled_reason,
    );
  }
}

export class DepositHold {
  constructor(
    public readonly id: string,
    public readonly recordId: number,
    public readonly source: string,
    public readonly kind: string,
    public readonly kindLabel: string,
    public readonly holdNumber: string,
    public readonly guestName: string,
    public readonly email: string,
    public readonly initials: string,
    public readonly phone: string,
    public readonly repeatGuest: boolean,
    public readonly guest: DepositGuest,
    public readonly reservation: DepositReservation,
    public readonly money: DepositMoney,
    public readonly provider: string,
    public readonly status: string,
    public readonly statusLabel: string,
    public readonly statusTone: DepositStatusTone,
    public readonly checkoutUrl: string,
    public readonly notes: string,
    public readonly adminUrl: string,
    public readonly inquiryAdminUrl: string,
    public readonly requestedDate: string,
    public readonly requestedTime: string,
    public readonly expirationDate: string,
    public readonly expirationTime: string,
    public readonly expirationTimeLeft: string,
    public readonly risk: string,
    public readonly riskTone: DepositRiskTone,
    public readonly hasWarning: boolean,
    public readonly timeline: DepositTimelineItem[],
    public readonly paymentAttempts: DepositPaymentAttempt[],
    public readonly receipt: DepositReceipt,
    public readonly canApprove: boolean,
    public readonly canRelease: boolean,
    public readonly canRequestGuestAction: boolean,
  ) {}

  static fromPayload(payload: DepositHoldPayload): DepositHold {
    return new DepositHold(
      payload.id,
      payload.record_id,
      payload.source,
      payload.kind,
      payload.kind_label,
      payload.hold_number,
      payload.guest_name,
      payload.email,
      payload.initials,
      payload.phone,
      payload.repeat_guest,
      DepositGuest.fromPayload(payload.guest),
      DepositReservation.fromPayload(payload.reservation),
      DepositMoney.fromPayload(payload.money),
      payload.provider,
      payload.status,
      payload.status_label,
      payload.status_tone,
      payload.checkout_url,
      payload.notes,
      payload.admin_url,
      payload.inquiry_admin_url,
      payload.requested.date,
      payload.requested.time,
      payload.expiration.date,
      payload.expiration.time,
      payload.expiration.time_left,
      payload.risk,
      payload.risk_tone,
      payload.has_warning,
      payload.timeline.map(DepositTimelineItem.fromPayload),
      payload.payment_attempts.map(DepositPaymentAttempt.fromPayload),
      DepositReceipt.fromPayload(payload.receipt),
      payload.actions.can_approve,
      payload.actions.can_release,
      payload.actions.can_request_guest_action,
    );
  }

  matches(query: string): boolean {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return true;
    return [
      this.guestName,
      this.email,
      this.holdNumber,
      this.reservation.listing,
      this.kindLabel,
      this.statusLabel,
    ].some((value) => value.toLowerCase().includes(normalized));
  }

  can(action: DepositHoldAction): boolean {
    if (action === 'approve') return this.canApprove;
    if (action === 'release') return this.canRelease;
    return this.canRequestGuestAction;
  }

  get holdDisplayNumber(): string {
    return `D-${String(this.recordId).padStart(4, '0')}`;
  }

  get fullHoldLabel(): string {
    return this.holdNumber;
  }
}

export class ExpiringDepositHold {
  constructor(
    public readonly id: string,
    public readonly guest: string,
    public readonly listing: string,
    public readonly timeLeft: string,
  ) {}

  static fromPayload(payload: ExpiringHoldPayload): ExpiringDepositHold {
    return new ExpiringDepositHold(payload.id, payload.guest, payload.listing, payload.time_left);
  }
}

export class DepositStatusOption {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly count: number,
  ) {}

  static fromPayload(payload: DepositStatusOptionPayload): DepositStatusOption {
    return new DepositStatusOption(payload.value, payload.label, payload.count);
  }
}

export class DepositHoldsSnapshot {
  constructor(
    public readonly summaryCards: DepositMetric[],
    public readonly statusOptions: DepositStatusOption[],
    public readonly rows: DepositHold[],
    public readonly expiringHolds: ExpiringDepositHold[],
    public readonly adminUrl: string,
    public readonly generatedAt: string,
  ) {}

  static fromPayload(payload: DepositHoldsSnapshotPayload): DepositHoldsSnapshot {
    return new DepositHoldsSnapshot(
      payload.summary_cards.map(DepositMetric.fromPayload),
      payload.status_options.map(DepositStatusOption.fromPayload),
      payload.rows.map(DepositHold.fromPayload),
      payload.expiring_holds.map(ExpiringDepositHold.fromPayload),
      payload.admin_url,
      payload.generated_at,
    );
  }
}
