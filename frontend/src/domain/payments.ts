import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type PaymentTone = 'green' | 'blue' | 'orange' | 'violet' | 'red' | 'slate' | 'cyan';

export interface PaymentMetricPayload {
  label: string;
  value: string | number;
  trend?: string;
  caption?: string;
  tone?: PaymentTone;
}

export interface PaymentRowPayload {
  id: string;
  transaction_id: string;
  guest: string;
  reservation: string;
  listing: string;
  channel: string;
  method: string;
  date_label: string;
  time_label: string;
  amount: string;
  status: string;
  status_cls: string;
  invoice_url: string;
  is_mock?: boolean;
}

export interface PaymentFilterOptionPayload {
  value: string;
  label: string;
  count: number;
}

export interface PaymentQuickActionPayload {
  label: string;
  kind: 'post' | 'link' | 'disabled';
  url?: string;
  action?: string;
  icon?: string;
  tone?: PaymentTone;
  disabled_reason?: string;
}

export interface PaymentInvoicePayload {
  id: string | number | null;
  number: string;
  status: string;
  issue_date: string;
  due_date: string;
  amount_due: string;
  view_url: string;
  download_url: string;
  can_download: boolean;
  disabled_reason: string;
}

export interface PaymentReservationPayload {
  id: string | number | null;
  request_key: string;
  listing: string;
  guest: string;
  date_range: string;
  view_url: string;
  selectable_url: string;
}

export interface PaymentGuestPayload {
  id: string | number | null;
  name: string;
  email: string;
  phone: string;
  view_url: string;
}

export interface PaymentDepositHistoryPayload {
  id: string | number | null;
  type: string;
  label: string;
  amount: string;
  status: string;
  status_cls: string;
  meta: string;
  view_url: string;
}

export interface PaymentDetailPayload extends Omit<PaymentRowPayload, 'reservation'> {
  invoice_number: string;
  issue_date: string;
  due_date: string;
  amount_due: string;
  invoice?: PaymentInvoicePayload;
  reservation?: PaymentReservationPayload;
  guest_detail?: PaymentGuestPayload;
  linked_reservation: {
    id?: string | number | null;
    request_key: string;
    listing: string;
    date_range: string;
    guest: string;
    url: string;
    view_url?: string;
    selectable_url?: string;
  };
  deposit_history: PaymentDepositHistoryPayload[];
  timeline: Array<{ label: string; meta: string; tone: string; action_label?: string; action_url?: string }>;
  notes: string;
  quick_actions: PaymentQuickActionPayload[];
}

export interface PaymentsWorkspaceFilters {
  search?: string;
  searchText?: string;
  status?: string;
  channel?: string;
  method?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export interface PaymentsPaginationPayload {
  page: number;
  page_size: number;
  total_pages: number;
  total_results: number;
  total_results_display?: string;
  start: number;
  end: number;
  has_previous: boolean;
  has_next: boolean;
  previous_page?: number | null;
  next_page?: number | null;
  pages?: Array<{ number: number; is_current: boolean; url?: string }>;
}

export interface PaymentsSnapshotPayload {
  summary_cards: PaymentMetricPayload[];
  rows: PaymentRowPayload[];
  detail: PaymentDetailPayload | null;
  transactions: unknown[];
  selected_transaction_id: string;
  total_results: number;
  generated_at: string;
  date_range_label?: string;
  filters?: Record<string, string>;
  filter_options?: {
    statuses?: PaymentFilterOptionPayload[];
    channels?: PaymentFilterOptionPayload[];
    methods?: PaymentFilterOptionPayload[];
    payment_types?: PaymentFilterOptionPayload[];
  };
  pagination?: PaymentsPaginationPayload;
  source?: 'api' | 'fallback' | 'mixed';
}

export interface PaymentRowProjection {
  id: string;
  transactionId: string;
  guest: string;
  reservation: string;
  listing: string;
  channel: string;
  method: string;
  dateLabel: string;
  timeLabel: string;
  amount: string;
  invoiceUrl: string;
  status: {
    label: string;
    tone: string;
  };
}

export class PaymentMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly trend: string,
    public readonly tone: PaymentTone,
  ) {}

  static fromPayload(payload: PaymentMetricPayload): PaymentMetric {
    return new PaymentMetric(
      payload.label,
      String(payload.value),
      payload.trend || payload.caption || 'Live ledger',
      payload.tone || 'blue',
    );
  }
}

export class PaymentTransaction {
  constructor(
    public readonly id: string,
    public readonly transactionId: string,
    public readonly guest: string,
    public readonly reservation: string,
    public readonly listing: string,
    public readonly channel: string,
    public readonly method: string,
    public readonly dateLabel: string,
    public readonly timeLabel: string,
    public readonly amount: string,
    public readonly status: string,
    public readonly statusTone: string,
    public readonly invoiceUrl: string,
    public readonly isMock: boolean,
  ) {}

  static fromPayload(payload: PaymentRowPayload): PaymentTransaction {
    return new PaymentTransaction(
      payload.id,
      payload.transaction_id,
      payload.guest,
      payload.reservation,
      payload.listing,
      payload.channel,
      payload.method,
      payload.date_label,
      payload.time_label,
      payload.amount,
      payload.status,
      payload.status_cls,
      payload.invoice_url,
      Boolean(payload.is_mock),
    );
  }

  rowProjection(): PaymentRowProjection {
    return {
      id: this.id,
      transactionId: this.transactionId,
      guest: this.guest,
      reservation: this.reservation,
      listing: this.listing,
      channel: this.channel,
      method: this.method,
      dateLabel: this.dateLabel,
      timeLabel: this.timeLabel,
      amount: this.amount,
      invoiceUrl: this.invoiceUrl,
      status: this.statusBadgeProjection(),
    };
  }

  statusBadgeProjection() {
    return {
      label: this.status,
      tone: this.statusTone,
    };
  }
}

export class PaymentDetail {
  constructor(private readonly payload: PaymentDetailPayload) {}

  rowProjection(): PaymentRowProjection {
    return PaymentTransaction.fromPayload({
      ...this.payload,
      reservation: this.payload.reservation?.request_key || this.payload.linked_reservation.request_key,
    }).rowProjection();
  }

  statusBadgeProjection() {
    return {
      label: this.payload.status,
      tone: this.payload.status_cls,
    };
  }

  invoiceProjection() {
    const invoice = this.payload.invoice;
    return {
      transactionId: this.payload.id,
      transactionNumber: this.payload.transaction_id,
      id: invoice?.id ?? null,
      invoiceNumber: invoice?.number || this.payload.invoice_number,
      status: invoice?.status || this.payload.status,
      invoiceUrl: invoice?.view_url || this.payload.invoice_url,
      issueDate: invoice?.issue_date || this.payload.issue_date,
      dueDate: invoice?.due_date || this.payload.due_date,
      amountDue: invoice?.amount_due || this.payload.amount_due,
      downloadUrl: invoice?.download_url || '',
      canDownload: Boolean(invoice?.can_download),
      disabledReason: invoice?.disabled_reason || 'Invoice download is not available.',
      amount: this.payload.amount,
      dateLabel: this.payload.date_label,
      timeLabel: this.payload.time_label,
    };
  }

  invoiceDocumentProjection() {
    const invoice = this.invoiceProjection();
    return {
      viewUrl: invoice.invoiceUrl,
      downloadUrl: invoice.downloadUrl,
      canDownload: invoice.canDownload,
      disabledReason: invoice.disabledReason,
    };
  }

  linkedReservationProjection() {
    const reservation = this.payload.reservation;
    if (reservation) return reservation;
    return {
      id: this.payload.linked_reservation.id ?? null,
      request_key: this.payload.linked_reservation.request_key,
      listing: this.payload.linked_reservation.listing,
      date_range: this.payload.linked_reservation.date_range,
      guest: this.payload.linked_reservation.guest,
      view_url: this.payload.linked_reservation.view_url || this.payload.linked_reservation.url,
      selectable_url: this.payload.linked_reservation.selectable_url || '',
    };
  }

  guestProjection() {
    return this.payload.guest_detail ?? {
      id: null,
      name: this.payload.guest,
      email: '',
      phone: '',
      view_url: '',
    };
  }

  depositHistoryProjection() {
    return this.payload.deposit_history;
  }

  timelineProjection() {
    return this.payload.timeline;
  }

  quickActionsProjection() {
    return this.payload.quick_actions;
  }

  notesProjection() {
    return this.payload.notes;
  }
}

export class PaymentsWorkspace {
  constructor(
    public readonly summaryCards: PaymentMetric[],
    public readonly transactions: PaymentTransaction[],
    public readonly selectedTransactionId: string,
    public readonly selectedDetail: PaymentDetail | null,
    public readonly totalResults: number,
    public readonly generatedAt: string,
    private readonly dateRangeLabelValue: string,
    private readonly filterOptionsPayload: NonNullable<PaymentsSnapshotPayload['filter_options']>,
    private readonly paginationPayload: PaymentsPaginationPayload,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}

  get source() {
    return this.metadata.source;
  }

  metricsProjection() {
    return this.summaryCards;
  }

  selectedTransaction(id = this.selectedTransactionId): PaymentTransaction | null {
    return this.transactions.find((transaction) => transaction.id === id) ?? null;
  }

  filteredTransactions(filters: PaymentsWorkspaceFilters = {}): PaymentTransaction[] {
    const search = (filters.searchText || filters.search || '').toLowerCase();
    return this.transactions.filter((transaction) => {
      const haystack = [
        transaction.transactionId,
        transaction.guest,
        transaction.reservation,
        transaction.listing,
        transaction.channel,
        transaction.method,
        transaction.status,
      ].join(' ').toLowerCase();
      if (search && !haystack.includes(search)) return false;
      if (filters.status && transaction.status !== filters.status) return false;
      if (filters.channel && transaction.channel !== filters.channel) return false;
      if (filters.method && transaction.method !== filters.method) return false;
      return true;
    });
  }

  dateRangeLabel() {
    return this.dateRangeLabelValue;
  }

  filterOptions() {
    return {
      statuses: this.filterOptionsPayload.statuses ?? [],
      channels: this.filterOptionsPayload.channels ?? [],
      methods: this.filterOptionsPayload.methods ?? [],
      paymentTypes: this.filterOptionsPayload.payment_types ?? [],
    };
  }

  paginationProjection() {
    return this.paginationPayload;
  }

  static fromPayload(payload: PaymentsSnapshotPayload): PaymentsWorkspace {
    const hasMockRows = payload.rows.some((row) => row.is_mock);
    const source = payload.source || (hasMockRows ? 'mixed' : 'api');
    return new PaymentsWorkspace(
      payload.summary_cards.map(PaymentMetric.fromPayload),
      payload.rows.map(PaymentTransaction.fromPayload),
      payload.selected_transaction_id,
      payload.detail ? new PaymentDetail(payload.detail) : null,
      payload.total_results,
      payload.generated_at,
      payload.date_range_label || 'Live ledger',
      payload.filter_options || {},
      payload.pagination || {
        page: 1,
        page_size: payload.rows.length || 10,
        total_pages: 1,
        total_results: payload.total_results,
        total_results_display: String(payload.total_results),
        start: payload.rows.length ? 1 : 0,
        end: payload.rows.length,
        has_previous: false,
        has_next: false,
      },
      createWorkspaceMetadata(source, hasMockRows ? ['live payment rows'] : []),
    );
  }
}
