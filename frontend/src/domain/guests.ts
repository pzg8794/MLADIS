import { createWorkspaceMetadata, WorkspaceObjectMetadata, WorkspaceDataSource } from './workspaceMetadata';

export type GuestTone = 'blue' | 'green' | 'orange' | 'red' | 'teal' | 'violet' | 'neutral' | 'warning' | 'danger' | 'success' | 'info';
export type GuestDetailTab = 'messages' | 'documents' | 'payments' | 'deposits' | 'activity';

export interface GuestMoneyPayload {
  amount_cents: number;
  currency: string;
  display: string;
  with_currency: string;
}

export interface GuestStatusPayload {
  value: string;
  label: string;
  tone: GuestTone;
}

export interface GuestTagPayload {
  label: string;
  slug: string;
  tone: GuestTone;
}

export interface GuestPreferencePayload {
  key: string;
  label: string;
  value: string;
  source: string;
}

export interface GuestMessagePayload {
  id: string;
  sender_label: string;
  body: string;
  status: string;
  timestamp: string;
  from_staff: boolean;
  requires_confirmation?: boolean;
}

export interface GuestDocumentPayload {
  id: string;
  title: string;
  type: string;
  status: string;
  url: string;
  created_at: string;
}

export interface GuestStayPayload {
  id: string;
  reservation_key: string;
  listing_name: string;
  date_range: string;
  total: GuestMoneyPayload;
  status: string;
  status_value: string;
  reservation_url: string;
  guests: number;
}

export interface GuestPaymentPayload {
  id: string;
  label: string;
  amount: GuestMoneyPayload;
  status: string;
  status_value: string;
  date: string;
  url: string;
}

export interface GuestPaymentsPayload {
  total_spend: GuestMoneyPayload;
  payment_count: number;
  last_payment_at: string;
  items: GuestPaymentPayload[];
}

export interface GuestDepositPayload {
  id: string;
  label: string;
  amount: GuestMoneyPayload;
  status: string;
  status_value: string;
  date: string;
  url: string;
}

export interface GuestDepositsPayload {
  active_holds: number;
  released_holds: number;
  dispute_count: number;
  items: GuestDepositPayload[];
}

export interface GuestTimelinePayload {
  type: string;
  label: string;
  actor: string;
  timestamp: string;
  note: string;
}

export interface GuestRowPayload {
  id: string;
  key: string;
  initials: string;
  name: string;
  email: string;
  phone: string;
  country: string;
  country_code: string;
  source: string;
  source_value: string;
  past_stays: number;
  total_spend: GuestMoneyPayload;
  status: GuestStatusPayload;
  segment: GuestStatusPayload;
  marketing_consent: string;
  last_contact_at: string;
  last_contact_label: string;
}

export interface GuestPayload {
  id: string;
  key: string;
  identity: {
    name: string;
    initials: string;
    country: string;
    country_code: string;
    preferred_language: string;
    source: string;
    source_label: string;
  };
  contact: {
    email: string;
    phone: string;
    last_contact_at: string;
    last_contact_label: string;
    profile_admin_url: string;
    full_profile_url: string;
  };
  profile: {
    birthday: string;
    travel_style: string;
    guest_since: string;
    notes: string;
    admin_url: string;
    full_profile_url: string;
  };
  status: GuestStatusPayload;
  segment: GuestStatusPayload;
  marketing: {
    consent_status: string;
    consent_label: string;
    requested_at: string;
    consent_at: string;
    can_receive_promotions: boolean;
  };
  tags: GuestTagPayload[];
  preferences: GuestPreferencePayload[];
  messages: { draft: string; items: GuestMessagePayload[] };
  documents: GuestDocumentPayload[];
  stays: GuestStayPayload[];
  payments: GuestPaymentsPayload;
  deposits: GuestDepositsPayload;
  timeline: GuestTimelinePayload[];
  row: GuestRowPayload;
  source: WorkspaceDataSource;
  missing_fields: string[];
  is_complete: boolean;
}

export interface GuestMetricPayload {
  label: string;
  value: string | number;
  caption: string;
  tone?: GuestTone;
}

export interface GuestSegmentTabPayload {
  value: string;
  label: string;
  count: number;
}

export interface GuestWorkspaceSnapshot {
  metrics: GuestMetricPayload[];
  summary_cards?: GuestMetricPayload[];
  segment_options: GuestSegmentTabPayload[];
  filters: Record<string, string>;
  rows: GuestPayload[];
  admin_url: string;
  legacy_url: string;
  generated_at: string;
  source: WorkspaceDataSource;
  missing_fields: string[];
  is_complete: boolean;
}

export interface GuestWorkspaceFilters {
  query?: string;
  segment?: string;
  source?: string;
  status?: string;
}

export class GuestMoney {
  constructor(
    public readonly cents: number,
    public readonly currency: string,
    public readonly display: string,
    public readonly withCurrency: string,
  ) {}

  static fromPayload(payload: GuestMoneyPayload): GuestMoney {
    return new GuestMoney(payload.amount_cents || 0, payload.currency || 'USD', payload.display || '$0', payload.with_currency || `${payload.display || '$0'} USD`);
  }
}

export class GuestStatus {
  constructor(
    public readonly value: string,
    public readonly label: string,
    public readonly tone: GuestTone,
  ) {}

  static fromPayload(payload: GuestStatusPayload): GuestStatus {
    return new GuestStatus(payload.value || 'active', payload.label || 'Active', payload.tone || 'neutral');
  }
}

export class GuestIdentity {
  constructor(
    public readonly name: string,
    public readonly initials: string,
    public readonly country: string,
    public readonly countryCode: string,
    public readonly preferredLanguage: string,
    public readonly source: string,
    public readonly sourceLabel: string,
  ) {}
}

export class GuestContact {
  constructor(
    public readonly email: string,
    public readonly phone: string,
    public readonly lastContactAt: string,
    public readonly lastContactLabel: string,
    public readonly profileAdminUrl: string,
    public readonly fullProfileUrl: string,
  ) {}

  get primary(): string {
    return this.email || this.phone || 'Needs contact details';
  }
}

export class GuestProfile {
  constructor(
    public readonly birthday: string,
    public readonly travelStyle: string,
    public readonly guestSince: string,
    public readonly notes: string,
    public readonly adminUrl: string,
    public readonly fullProfileUrl: string,
  ) {}
}

export class GuestMarketing {
  constructor(
    public readonly consentStatus: string,
    public readonly consentLabel: string,
    public readonly requestedAt: string,
    public readonly consentAt: string,
    public readonly canReceivePromotions: boolean,
  ) {}
}

export class GuestTag {
  constructor(
    public readonly label: string,
    public readonly slug: string,
    public readonly tone: GuestTone,
  ) {}

  static fromPayload(payload: GuestTagPayload): GuestTag {
    return new GuestTag(payload.label, payload.slug, payload.tone || 'neutral');
  }
}

export class GuestPreference {
  constructor(
    public readonly key: string,
    public readonly label: string,
    public readonly value: string,
    public readonly source: string,
  ) {}

  static fromPayload(payload: GuestPreferencePayload): GuestPreference {
    return new GuestPreference(payload.key, payload.label, payload.value, payload.source);
  }
}

export class GuestMessageThread {
  constructor(
    public readonly draft: string,
    public readonly items: GuestMessagePayload[],
  ) {}
}

export class GuestPaymentProjection {
  constructor(
    public readonly totalSpend: GuestMoney,
    public readonly paymentCount: number,
    public readonly lastPaymentAt: string,
    public readonly items: GuestPaymentPayload[],
  ) {}
}

export class GuestDepositProjection {
  constructor(
    public readonly activeHolds: number,
    public readonly releasedHolds: number,
    public readonly disputeCount: number,
    public readonly items: GuestDepositPayload[],
  ) {}
}

export class Guest {
  constructor(
    public readonly id: string,
    public readonly key: string,
    public readonly identity: GuestIdentity,
    public readonly contact: GuestContact,
    public readonly profile: GuestProfile,
    public readonly status: GuestStatus,
    public readonly segment: GuestStatus,
    public readonly marketing: GuestMarketing,
    public readonly tags: GuestTag[],
    public readonly preferences: GuestPreference[],
    public readonly messages: GuestMessageThread,
    public readonly documents: GuestDocumentPayload[],
    public readonly stays: GuestStayPayload[],
    public readonly payments: GuestPaymentProjection,
    public readonly deposits: GuestDepositProjection,
    public readonly timeline: GuestTimelinePayload[],
    public readonly row: GuestRowPayload,
    public readonly source: WorkspaceDataSource,
    public readonly missingFields: string[],
    public readonly isComplete: boolean,
  ) {}

  static fromPayload(payload: GuestPayload): Guest {
    return new Guest(
      payload.id,
      payload.key,
      new GuestIdentity(
        payload.identity.name,
        payload.identity.initials,
        payload.identity.country,
        payload.identity.country_code,
        payload.identity.preferred_language,
        payload.identity.source,
        payload.identity.source_label,
      ),
      new GuestContact(
        payload.contact.email,
        payload.contact.phone,
        payload.contact.last_contact_at,
        payload.contact.last_contact_label,
        payload.contact.profile_admin_url,
        payload.contact.full_profile_url,
      ),
      new GuestProfile(
        payload.profile.birthday,
        payload.profile.travel_style,
        payload.profile.guest_since,
        payload.profile.notes,
        payload.profile.admin_url,
        payload.profile.full_profile_url,
      ),
      GuestStatus.fromPayload(payload.status),
      GuestStatus.fromPayload(payload.segment),
      new GuestMarketing(
        payload.marketing.consent_status,
        payload.marketing.consent_label,
        payload.marketing.requested_at,
        payload.marketing.consent_at,
        payload.marketing.can_receive_promotions,
      ),
      payload.tags.map(GuestTag.fromPayload),
      payload.preferences.map(GuestPreference.fromPayload),
      new GuestMessageThread(payload.messages.draft || '', payload.messages.items),
      payload.documents,
      payload.stays,
      new GuestPaymentProjection(
        GuestMoney.fromPayload(payload.payments.total_spend),
        payload.payments.payment_count,
        payload.payments.last_payment_at,
        payload.payments.items,
      ),
      new GuestDepositProjection(
        payload.deposits.active_holds,
        payload.deposits.released_holds,
        payload.deposits.dispute_count,
        payload.deposits.items,
      ),
      payload.timeline,
      payload.row,
      payload.source || 'api',
      payload.missing_fields || [],
      Boolean(payload.is_complete),
    );
  }

  get displayName(): string {
    return this.identity.name;
  }

  get isBlocked(): boolean {
    return this.status.value === 'blocked' || this.segment.value === 'blacklisted';
  }

  get isVip(): boolean {
    return !this.isBlocked && this.segment.value === 'vip';
  }

  get isRepeatGuest(): boolean {
    return !this.isBlocked && (this.segment.value === 'repeat' || this.row.past_stays >= 2);
  }

  get canMessage(): boolean {
    return !this.isBlocked && Boolean(this.contact.email || this.contact.phone);
  }

  rowProjection(): GuestRowPayload {
    return this.row;
  }

  profileProjection(): GuestProfile {
    return this.profile;
  }

  messageProjection(): GuestMessageThread {
    return this.messages;
  }

  documentsProjection(): GuestDocumentPayload[] {
    return this.documents;
  }

  paymentsProjection(): GuestPaymentProjection {
    return this.payments;
  }

  depositsProjection(): GuestDepositProjection {
    return this.deposits;
  }

  activityProjection(): GuestTimelinePayload[] {
    return this.timeline;
  }

  staysProjection(): GuestStayPayload[] {
    return this.stays;
  }

  matches(query: string): boolean {
    const needle = query.trim().toLowerCase();
    if (!needle) return true;
    return [
      this.displayName,
      this.contact.email,
      this.contact.phone,
      this.identity.country,
      this.identity.sourceLabel,
      this.segment.label,
      this.profile.notes,
      ...this.tags.map((tag) => tag.label),
    ].some((value) => value.toLowerCase().includes(needle));
  }
}

export class GuestMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly tone: GuestTone,
  ) {}

  static fromPayload(payload: GuestMetricPayload): GuestMetric {
    return new GuestMetric(payload.label, String(payload.value), payload.caption || 'Guest intelligence', payload.tone || 'blue');
  }
}

export class GuestWorkspace {
  constructor(
    public readonly guests: Guest[],
    public readonly metrics: GuestMetric[],
    public readonly tabs: GuestSegmentTabPayload[],
    public readonly filters: Record<string, string>,
    public readonly adminUrl: string,
    public readonly legacyUrl: string,
    public readonly generatedAt: string,
    public readonly metadata: WorkspaceObjectMetadata,
  ) {}

  static fromPayload(payload: GuestWorkspaceSnapshot): GuestWorkspace {
    return new GuestWorkspace(
      payload.rows.map(Guest.fromPayload),
      (payload.metrics || payload.summary_cards || []).map(GuestMetric.fromPayload),
      payload.segment_options || [],
      payload.filters || {},
      payload.admin_url,
      payload.legacy_url,
      payload.generated_at,
      createWorkspaceMetadata(payload.source || 'api', payload.missing_fields || []),
    );
  }

  metricsProjection(): GuestMetric[] {
    return this.metrics;
  }

  segmentTabs(): GuestSegmentTabPayload[] {
    return this.tabs.length ? this.tabs : [
      { value: 'all', label: 'All', count: this.guests.length },
      { value: 'repeat', label: 'Repeat Guests', count: this.guests.filter((guest) => guest.isRepeatGuest).length },
      { value: 'vip', label: 'VIP', count: this.guests.filter((guest) => guest.isVip).length },
      { value: 'new', label: 'New', count: this.guests.filter((guest) => guest.segment.value === 'new').length },
      { value: 'blocked', label: 'Blocked', count: this.guests.filter((guest) => guest.isBlocked).length },
    ];
  }

  filteredGuests(filters: GuestWorkspaceFilters): Guest[] {
    const segment = filters.segment || 'all';
    return this.guests.filter((guest) => {
      const matchesSegment =
        !segment ||
        segment === 'all' ||
        (segment === 'repeat' && guest.isRepeatGuest) ||
        (segment === 'blocked' && guest.isBlocked) ||
        guest.segment.value === segment;
      const matchesStatus = !filters.status || guest.status.value === filters.status;
      const matchesSource = !filters.source || guest.identity.source === filters.source;
      return matchesSegment && matchesStatus && matchesSource && guest.matches(filters.query || '');
    });
  }

  selectedGuest(id?: string): Guest | null {
    if (!id) return this.guests[0] ?? null;
    return this.guests.find((guest) => guest.id === id || guest.key === id) ?? this.guests[0] ?? null;
  }
}
