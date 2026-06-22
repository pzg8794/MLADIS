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

export interface PaymentQuickActionPayload {
  label: string;
  kind: 'post' | 'link' | 'disabled';
  url?: string;
  action?: string;
  icon?: string;
  tone?: PaymentTone;
  disabled_reason?: string;
}

export interface PaymentDetailPayload {
  transaction_id: string;
  status: string;
  status_cls: string;
  amount: string;
  date_label: string;
  time_label: string;
  invoice_number: string;
  invoice_url: string;
  issue_date: string;
  due_date: string;
  amount_due: string;
  linked_reservation: {
    request_key: string;
    listing: string;
    date_range: string;
    guest: string;
    url: string;
  };
  deposit_history: Array<{ label: string; amount: string; status: string; status_cls: string; meta: string }>;
  timeline: Array<{ label: string; meta: string; tone: string; action_label: string; action_url: string }>;
  notes: string;
  quick_actions: PaymentQuickActionPayload[];
}

export interface PaymentsSnapshotPayload {
  summary_cards: PaymentMetricPayload[];
  rows: PaymentRowPayload[];
  detail: PaymentDetailPayload | null;
  transactions: unknown[];
  selected_transaction_id: string;
  total_results: number;
  generated_at: string;
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
}

export class PaymentDetail {
  constructor(public readonly payload: PaymentDetailPayload) {}
}

export class PaymentsWorkspace {
  constructor(
    public readonly summaryCards: PaymentMetric[],
    public readonly transactions: PaymentTransaction[],
    public readonly selectedTransactionId: string,
    public readonly selectedDetail: PaymentDetail | null,
    public readonly totalResults: number,
    public readonly generatedAt: string,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}

  get source() {
    return this.metadata.source;
  }

  selectedTransaction(): PaymentTransaction | null {
    return this.transactions.find((transaction) => transaction.id === this.selectedTransactionId) ?? this.transactions[0] ?? null;
  }

  static fromPayload(payload: PaymentsSnapshotPayload): PaymentsWorkspace {
    const hasMockRows = payload.rows.some((row) => row.is_mock);
    return new PaymentsWorkspace(
      payload.summary_cards.map(PaymentMetric.fromPayload),
      payload.rows.map(PaymentTransaction.fromPayload),
      payload.selected_transaction_id,
      payload.detail ? new PaymentDetail(payload.detail) : null,
      payload.total_results,
      payload.generated_at,
      createWorkspaceMetadata(hasMockRows ? 'mixed' : 'api', hasMockRows ? ['live payment rows'] : []),
    );
  }
}
