import {
  OpsAgentConversation,
  OpsAgentFaq,
  OpsAgentSnapshot,
  OpsAgentTopic,
  OpsChart,
  OpsChartRow,
  OpsCustomerRow,
  OpsCustomersSnapshot,
  OpsDepositRow,
  OpsDepositStatusOption,
  OpsDepositsSnapshot,
  OpsMetric,
  OpsReportsSnapshot,
  OpsSegmentOption,
} from '../domain/models';
import { HttpClient } from './HttpClient';

interface ApiOpsMetric {
  label: string;
  value: string | number;
  caption: string;
}

interface ApiOpsChartRow {
  label: string;
  total: number;
  width: number;
}

interface ApiOpsChart {
  id: string;
  title: string;
  category: string;
  rows: ApiOpsChartRow[];
  max_total: number;
}

interface ApiOpsReportsSnapshot {
  summary_cards: ApiOpsMetric[];
  charts: ApiOpsChart[];
  report_since: string;
  report_until: string;
  legacy_url: string;
  calendar_url: string;
}

interface ApiOpsSegmentOption {
  value: string;
  label: string;
  count: number;
  url: string;
}

interface ApiOpsCustomerRow {
  id: number;
  name: string;
  email: string;
  phone: string;
  segment: string;
  segment_value: string;
  source: string;
  marketing_consent: string;
  can_receive_promotions: boolean;
  direct_reservations: number;
  airbnb_reservations: number;
  feedback_count: number;
  invoice_count: number;
  last_stay: string;
  notes: string;
  admin_url: string;
  updated_at: string;
}

interface ApiOpsCustomersSnapshot {
  summary_cards: ApiOpsMetric[];
  segment_options: ApiOpsSegmentOption[];
  rows: ApiOpsCustomerRow[];
  admin_url: string;
  legacy_url: string;
  generated_at: string;
}

interface ApiOpsDepositStatusOption {
  value: string;
  label: string;
  count: number;
}

interface ApiOpsDepositRow {
  id: number;
  guest_name: string;
  email: string;
  stay_name: string;
  amount: string;
  provider: string;
  status: string;
  status_label: string;
  checkout_url: string;
  notes: string;
  admin_url: string;
  inquiry_admin_url: string;
  created_label: string;
  updated_at: string;
}

interface ApiOpsDepositsSnapshot {
  summary_cards: ApiOpsMetric[];
  status_options: ApiOpsDepositStatusOption[];
  rows: ApiOpsDepositRow[];
  admin_url: string;
  generated_at: string;
}

interface ApiOpsAgentTopic {
  label: string;
  value: string;
  total: number;
  width: number;
}

interface ApiOpsAgentConversation {
  id: number;
  topic: string;
  mode: string;
  item: string;
  visitor: string;
  last_question: string;
  last_reply: string;
  language: string;
  admin_url: string;
  updated_at: string;
}

interface ApiOpsAgentFaq {
  id: number;
  question: string;
  answer: string;
  category: string;
  keywords: string;
  item: string;
  language: string;
  min_score: string;
  priority: number;
  is_active: boolean;
  admin_url: string;
  updated_at: string;
}

interface ApiOpsAgentSnapshot {
  summary_cards: ApiOpsMetric[];
  topics: ApiOpsAgentTopic[];
  conversations: ApiOpsAgentConversation[];
  faqs: ApiOpsAgentFaq[];
  faq_admin_url: string;
  conversation_admin_url: string;
  generated_at: string;
}

export interface OpsWorkspaceRepository {
  getReports(): Promise<OpsReportsSnapshot>;
  getCustomers(): Promise<OpsCustomersSnapshot>;
  getDeposits(): Promise<OpsDepositsSnapshot>;
  getAgent(): Promise<OpsAgentSnapshot>;
}

export class ApiOpsWorkspaceRepository implements OpsWorkspaceRepository {
  constructor(private readonly http: HttpClient) {}

  async getReports(): Promise<OpsReportsSnapshot> {
    const data = await this.http.get<ApiOpsReportsSnapshot>('/api/ops/reports/');
    return new OpsReportsSnapshot(
      data.summary_cards.map(toMetric),
      data.charts.map((chart) => new OpsChart(
        chart.id,
        chart.title,
        chart.category,
        chart.rows.map((row) => new OpsChartRow(row.label, row.total, row.width)),
        chart.max_total,
      )),
      data.report_since,
      data.report_until,
      data.legacy_url,
      data.calendar_url,
    );
  }

  async getCustomers(): Promise<OpsCustomersSnapshot> {
    const data = await this.http.get<ApiOpsCustomersSnapshot>('/api/ops/customers/');
    return new OpsCustomersSnapshot(
      data.summary_cards.map(toMetric),
      data.segment_options.map((segment) => new OpsSegmentOption(segment.value, segment.label, segment.count, segment.url)),
      data.rows.map((row) => new OpsCustomerRow(
        row.id,
        row.name,
        row.email,
        row.phone,
        row.segment,
        row.segment_value,
        row.source,
        row.marketing_consent,
        row.can_receive_promotions,
        row.direct_reservations,
        row.airbnb_reservations,
        row.feedback_count,
        row.invoice_count,
        row.last_stay,
        row.notes,
        row.admin_url,
        row.updated_at,
      )),
      data.admin_url,
      data.legacy_url,
      data.generated_at,
    );
  }

  async getDeposits(): Promise<OpsDepositsSnapshot> {
    const data = await this.http.get<ApiOpsDepositsSnapshot>('/api/ops/deposits/');
    return new OpsDepositsSnapshot(
      data.summary_cards.map(toMetric),
      data.status_options.map((status) => new OpsDepositStatusOption(status.value, status.label, status.count)),
      data.rows.map((row) => new OpsDepositRow(
        row.id,
        row.guest_name,
        row.email,
        row.stay_name,
        row.amount,
        row.provider,
        row.status,
        row.status_label,
        row.checkout_url,
        row.notes,
        row.admin_url,
        row.inquiry_admin_url,
        row.created_label,
        row.updated_at,
      )),
      data.admin_url,
      data.generated_at,
    );
  }

  async getAgent(): Promise<OpsAgentSnapshot> {
    const data = await this.http.get<ApiOpsAgentSnapshot>('/api/ops/agent/');
    return new OpsAgentSnapshot(
      data.summary_cards.map(toMetric),
      data.topics.map((topic) => new OpsAgentTopic(topic.label, topic.value, topic.total, topic.width)),
      data.conversations.map((row) => new OpsAgentConversation(
        row.id,
        row.topic,
        row.mode,
        row.item,
        row.visitor,
        row.last_question,
        row.last_reply,
        row.language,
        row.admin_url,
        row.updated_at,
      )),
      data.faqs.map((row) => new OpsAgentFaq(
        row.id,
        row.question,
        row.answer,
        row.category,
        row.keywords,
        row.item,
        row.language,
        row.min_score,
        row.priority,
        row.is_active,
        row.admin_url,
        row.updated_at,
      )),
      data.faq_admin_url,
      data.conversation_admin_url,
      data.generated_at,
    );
  }
}

function toMetric(item: ApiOpsMetric): OpsMetric {
  return new OpsMetric(item.label, String(item.value), item.caption);
}
