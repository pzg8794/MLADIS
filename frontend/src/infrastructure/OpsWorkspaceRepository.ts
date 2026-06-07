import {
  OpsAgentConversation,
  OpsAgentFaq,
  OpsAgentSnapshot,
  OpsAgentTopic,
  OpsChart,
  OpsChartRow,
  OpsCalendarDay,
  OpsCalendarEvent,
  OpsCalendarEventType,
  OpsCalendarSnapshot,
  OpsCalendarStay,
  OpsCalendarStayRow,
  OpsCalendarViewMode,
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

interface ApiOpsCalendarStay {
  id: number;
  name: string;
  slug: string;
  subtitle: string;
  default_price: string;
  is_configured: boolean;
  feed_label: string;
  feed_status: string;
  last_checked_at: string;
}

interface ApiOpsCalendarDay {
  date: string;
  day: number;
  weekday: string;
  label: string;
  in_month: boolean;
  is_today: boolean;
  status: string;
  reservation_count: number;
  block_count: number;
  has_price_override: boolean;
  price_display: string;
  price_source: string;
  price_label: string;
}

interface ApiOpsCalendarEvent {
  id: string;
  record_id: number;
  type: OpsCalendarEventType;
  title: string;
  subtitle: string;
  item_id: number;
  item_name: string;
  start: string;
  end: string;
  range_label: string;
  status: string;
  guest_label: string;
  amount: string;
  admin_url: string;
}

interface ApiOpsCalendarSnapshot {
  view: OpsCalendarViewMode;
  focus_date: string;
  month_label: string;
  visible_start: string;
  visible_end: string;
  previous_date: string;
  next_date: string;
  selected_item_id: number | null;
  stays: ApiOpsCalendarStay[];
  summary_cards: ApiOpsMetric[];
  weeks: ApiOpsCalendarDay[][];
  week_days: ApiOpsCalendarDay[];
  stay_rows: ApiOpsCalendarStayRow[];
  events: ApiOpsCalendarEvent[];
  agenda: ApiOpsCalendarEvent[];
  admin_records_url: string;
  generated_at: string;
}

interface ApiOpsCalendarStayRow {
  stay: ApiOpsCalendarStay;
  week_days: ApiOpsCalendarDay[];
  weeks: ApiOpsCalendarDay[][];
  events: ApiOpsCalendarEvent[];
}

export interface OpsCalendarQuery {
  itemId?: number | null;
  view?: OpsCalendarViewMode;
  date?: string;
}

export interface OpsCalendarBlockInput {
  item: number;
  start_date: string;
  end_date: string;
  reason: string;
  notes: string;
}

export interface OpsCalendarPriceInput {
  item: number;
  start_date: string;
  end_date: string;
  nightly_price: string;
  label: string;
  notes: string;
}

export interface OpsWorkspaceRepository {
  getReports(): Promise<OpsReportsSnapshot>;
  getCustomers(): Promise<OpsCustomersSnapshot>;
  getDeposits(): Promise<OpsDepositsSnapshot>;
  getAgent(): Promise<OpsAgentSnapshot>;
  getCalendar(query: OpsCalendarQuery): Promise<OpsCalendarSnapshot>;
  createCalendarBlock(input: OpsCalendarBlockInput): Promise<void>;
  deleteCalendarBlock(id: number): Promise<void>;
  createCalendarPrice(input: OpsCalendarPriceInput): Promise<void>;
  deleteCalendarPrice(id: number): Promise<void>;
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

  async getCalendar(query: OpsCalendarQuery): Promise<OpsCalendarSnapshot> {
    const params = new URLSearchParams();
    if (query.itemId) params.set('item', String(query.itemId));
    if (query.view) params.set('view', query.view);
    if (query.date) params.set('date', query.date);
    const path = params.toString() ? `/api/ops/calendar/?${params}` : '/api/ops/calendar/';
    const data = await this.http.get<ApiOpsCalendarSnapshot>(path);
    return new OpsCalendarSnapshot(
      data.view,
      data.focus_date,
      data.month_label,
      data.visible_start,
      data.visible_end,
      data.previous_date,
      data.next_date,
      data.selected_item_id,
      data.stays.map(toCalendarStay),
      data.summary_cards.map(toMetric),
      data.weeks.map((week) => week.map(toCalendarDay)),
      data.week_days.map(toCalendarDay),
      data.stay_rows.map(toCalendarStayRow),
      data.events.map(toCalendarEvent),
      data.agenda.map(toCalendarEvent),
      data.admin_records_url,
      data.generated_at,
    );
  }

  async createCalendarBlock(input: OpsCalendarBlockInput): Promise<void> {
    await this.http.post('/api/ops/calendar/blocks/', input);
  }

  async deleteCalendarBlock(id: number): Promise<void> {
    await this.http.delete('/api/ops/calendar/blocks/', { id });
  }

  async createCalendarPrice(input: OpsCalendarPriceInput): Promise<void> {
    await this.http.post('/api/ops/calendar/prices/', input);
  }

  async deleteCalendarPrice(id: number): Promise<void> {
    await this.http.delete('/api/ops/calendar/prices/', { id });
  }
}

function toCalendarStayRow(item: ApiOpsCalendarStayRow): OpsCalendarStayRow {
  return new OpsCalendarStayRow(
    toCalendarStay(item.stay),
    item.week_days.map(toCalendarDay),
    item.weeks.map((week) => week.map(toCalendarDay)),
    item.events.map(toCalendarEvent),
  );
}

function toMetric(item: ApiOpsMetric): OpsMetric {
  return new OpsMetric(item.label, String(item.value), item.caption);
}

function toCalendarStay(item: ApiOpsCalendarStay): OpsCalendarStay {
  return new OpsCalendarStay(
    item.id,
    item.name,
    item.slug,
    item.subtitle,
    item.default_price,
    item.is_configured,
    item.feed_label,
    item.feed_status,
    item.last_checked_at,
  );
}

function toCalendarDay(item: ApiOpsCalendarDay): OpsCalendarDay {
  return new OpsCalendarDay(
    item.date,
    item.day,
    item.weekday,
    item.label,
    item.in_month,
    item.is_today,
    item.status,
    item.reservation_count,
    item.block_count,
    item.has_price_override,
    item.price_display,
    item.price_source,
    item.price_label,
  );
}

function toCalendarEvent(item: ApiOpsCalendarEvent): OpsCalendarEvent {
  return new OpsCalendarEvent(
    item.id,
    item.record_id,
    item.type,
    item.title,
    item.subtitle,
    item.item_id,
    item.item_name,
    item.start,
    item.end,
    item.range_label,
    item.status,
    item.guest_label,
    item.amount,
    item.admin_url,
  );
}
