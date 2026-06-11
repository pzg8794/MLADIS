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
  OpsMaintenanceEvent,
  OpsMaintenanceOption,
  OpsMaintenancePhoto,
  OpsMaintenanceSnapshot,
  OpsMaintenanceStay,
  OpsMetric,
  OpsReportsSnapshot,
  OpsSegmentOption,
  OpsWorkboardSnapshot,
  OpsWorkItem,
  OpsWorkItemList,
  OpsWorkStatusColumn,
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

interface ApiOpsMaintenanceOption {
  value: string;
  label: string;
  count: number;
}

interface ApiOpsMaintenanceStay {
  id: number;
  name: string;
  slug: string;
  subtitle: string;
  max_guests: number;
}

interface ApiOpsMaintenancePhoto {
  id: string;
  url: string;
  caption: string;
  sort_order: number;
  is_cover: boolean;
  mime_type: string;
  file_size_bytes: number;
  checksum_sha256: string;
  uploaded_at: string;
}

interface ApiOpsMaintenanceEvent {
  id: string;
  title: string;
  item_id: number;
  item_name: string;
  booking_id: number | null;
  work_type: string;
  work_type_label: string;
  status: string;
  status_label: string;
  payment_status: string;
  payment_status_label: string;
  display_cost: string;
  cost_amount: string;
  cost_currency: string;
  reported_at: string;
  reported_label: string;
  started_at: string;
  completed_at: string;
  duration_minutes: number | null;
  vendor_name: string;
  vendor_contact: string;
  invoice_number: string;
  proof_of_payment_ref: string;
  tax_category_code: string;
  description: string;
  ai_description: string;
  ai_description_generated_at: string;
  ai_description_model: string;
  ai_description_metadata: Record<string, unknown>;
  use_ai_description: boolean;
  admin_notes: string;
  photo_count: number;
  first_photo_url: string;
  is_tax_ready: boolean;
  created_by: string;
  admin_url: string;
  agent_payload_url: string;
  ai_description_url: string;
  photos: ApiOpsMaintenancePhoto[];
  created_at: string;
  updated_at: string;
}

interface ApiOpsMaintenanceSnapshot {
  summary_cards: ApiOpsMetric[];
  work_type_options: ApiOpsMaintenanceOption[];
  status_options: ApiOpsMaintenanceOption[];
  payment_status_options: ApiOpsMaintenanceOption[];
  stays: ApiOpsMaintenanceStay[];
  rows: ApiOpsMaintenanceEvent[];
  admin_url: string;
  add_admin_url: string;
  generated_at: string;
}

interface ApiOpsWorkItem {
  id: number;
  title: string;
  description: string;
  list_name: string;
  neuron: string;
  neuron_label: string;
  status: string;
  status_label: string;
  priority: string;
  priority_label: string;
  next_action: string;
  source_url: string;
  github_url: string;
  drive_url: string;
  due_date: string;
  completed_at: string;
  updated_at: string;
  is_done: boolean;
}

interface ApiOpsWorkItemList {
  name: string;
  total: number;
  done: number;
  open: number;
  items: ApiOpsWorkItem[];
}

interface ApiOpsWorkStatusColumn {
  status: string;
  label: string;
  items: ApiOpsWorkItem[];
}

interface ApiOpsWorkboardSnapshot {
  summary_cards: ApiOpsMetric[];
  lists: ApiOpsWorkItemList[];
  status_columns: ApiOpsWorkStatusColumn[];
  focus_items: ApiOpsWorkItem[];
  generated_at: string;
}

interface ApiOpsWorkItemCompletionResponse {
  ok: boolean;
  item: ApiOpsWorkItem;
}

interface ApiOpsMaintenanceCreateResponse {
  ok: boolean;
  message: string;
  event: ApiOpsMaintenanceEvent;
}

interface ApiOpsMaintenanceAIDescriptionResponse {
  ok: boolean;
  message: string;
  event: ApiOpsMaintenanceEvent;
}

export interface OpsMaintenanceDraftAiDescriptionResult {
  ok: boolean;
  message: string;
  description: string;
  observations: string[];
  confidence: string;
  model: string;
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
  getWorkboard(): Promise<OpsWorkboardSnapshot>;
  setWorkItemCompletion(id: number, completed: boolean): Promise<OpsWorkItem>;
  getReports(): Promise<OpsReportsSnapshot>;
  getCustomers(): Promise<OpsCustomersSnapshot>;
  getDeposits(): Promise<OpsDepositsSnapshot>;
  getAgent(): Promise<OpsAgentSnapshot>;
  getCalendar(query: OpsCalendarQuery): Promise<OpsCalendarSnapshot>;
  getMaintenance(): Promise<OpsMaintenanceSnapshot>;
  createMaintenanceEvent(input: FormData): Promise<OpsMaintenanceEvent>;
  getMaintenanceAgentPayload(id: string): Promise<Record<string, unknown>>;
  generateMaintenanceAiDescription(id: string): Promise<OpsMaintenanceEvent>;
  generateMaintenanceDraftAiDescription(input: FormData): Promise<OpsMaintenanceDraftAiDescriptionResult>;
  createCalendarBlock(input: OpsCalendarBlockInput): Promise<void>;
  deleteCalendarBlock(id: number): Promise<void>;
  createCalendarPrice(input: OpsCalendarPriceInput): Promise<void>;
  deleteCalendarPrice(id: number): Promise<void>;
}

export class ApiOpsWorkspaceRepository implements OpsWorkspaceRepository {
  constructor(private readonly http: HttpClient) {}

  async getWorkboard(): Promise<OpsWorkboardSnapshot> {
    const data = await this.http.get<ApiOpsWorkboardSnapshot>('/api/ops/workboard/');
    return new OpsWorkboardSnapshot(
      data.summary_cards.map(toMetric),
      data.lists.map((list) => new OpsWorkItemList(
        list.name,
        list.total,
        list.done,
        list.open,
        list.items.map(toWorkItem),
      )),
      data.status_columns.map((column) => new OpsWorkStatusColumn(
        column.status,
        column.label,
        column.items.map(toWorkItem),
      )),
      data.focus_items.map(toWorkItem),
      data.generated_at,
    );
  }

  async setWorkItemCompletion(id: number, completed: boolean): Promise<OpsWorkItem> {
    const data = await this.http.post<ApiOpsWorkItemCompletionResponse>(
      `/api/ops/workboard/items/${id}/completion/`,
      { completed },
    );
    return toWorkItem(data.item);
  }

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

  async getMaintenance(): Promise<OpsMaintenanceSnapshot> {
    const data = await this.http.get<ApiOpsMaintenanceSnapshot>('/api/ops/maintenance/');
    return new OpsMaintenanceSnapshot(
      data.summary_cards.map(toMetric),
      data.work_type_options.map(toMaintenanceOption),
      data.status_options.map(toMaintenanceOption),
      data.payment_status_options.map(toMaintenanceOption),
      data.stays.map(toMaintenanceStay),
      data.rows.map(toMaintenanceEvent),
      data.admin_url,
      data.add_admin_url,
      data.generated_at,
    );
  }

  async createMaintenanceEvent(input: FormData): Promise<OpsMaintenanceEvent> {
    const data = await this.http.postForm<ApiOpsMaintenanceCreateResponse>('/api/ops/maintenance/', input);
    return toMaintenanceEvent(data.event);
  }

  async getMaintenanceAgentPayload(id: string): Promise<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`/api/ops/maintenance/${id}/agent-payload/`);
  }

  async generateMaintenanceAiDescription(id: string): Promise<OpsMaintenanceEvent> {
    const data = await this.http.post<ApiOpsMaintenanceAIDescriptionResponse>(`/api/ops/maintenance/${id}/ai-description/`, {});
    return toMaintenanceEvent(data.event);
  }

  async generateMaintenanceDraftAiDescription(input: FormData): Promise<OpsMaintenanceDraftAiDescriptionResult> {
    return this.http.postForm<OpsMaintenanceDraftAiDescriptionResult>('/api/ops/maintenance/ai-description/draft/', input);
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

function toWorkItem(item: ApiOpsWorkItem): OpsWorkItem {
  return new OpsWorkItem(
    item.id,
    item.title,
    item.description,
    item.list_name,
    item.neuron,
    item.neuron_label,
    item.status,
    item.status_label,
    item.priority,
    item.priority_label,
    item.next_action,
    item.source_url,
    item.github_url,
    item.drive_url,
    item.due_date,
    item.completed_at,
    item.updated_at,
    item.is_done,
  );
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

function toMaintenanceOption(item: ApiOpsMaintenanceOption): OpsMaintenanceOption {
  return new OpsMaintenanceOption(item.value, item.label, item.count);
}

function toMaintenanceStay(item: ApiOpsMaintenanceStay): OpsMaintenanceStay {
  return new OpsMaintenanceStay(
    item.id,
    item.name,
    item.slug,
    item.subtitle,
    item.max_guests,
  );
}

function toMaintenancePhoto(item: ApiOpsMaintenancePhoto): OpsMaintenancePhoto {
  return new OpsMaintenancePhoto(
    item.id,
    item.url,
    item.caption,
    item.sort_order,
    item.is_cover,
    item.mime_type,
    item.file_size_bytes,
    item.checksum_sha256,
    item.uploaded_at,
  );
}

function toMaintenanceEvent(item: ApiOpsMaintenanceEvent): OpsMaintenanceEvent {
  return new OpsMaintenanceEvent(
    item.id,
    item.title,
    item.item_id,
    item.item_name,
    item.booking_id,
    item.work_type,
    item.work_type_label,
    item.status,
    item.status_label,
    item.payment_status,
    item.payment_status_label,
    item.display_cost,
    item.cost_amount,
    item.cost_currency,
    item.reported_at,
    item.reported_label,
    item.started_at,
    item.completed_at,
    item.duration_minutes,
    item.vendor_name,
    item.vendor_contact,
    item.invoice_number,
    item.proof_of_payment_ref,
    item.tax_category_code,
    item.description,
    item.ai_description,
    item.ai_description_generated_at,
    item.ai_description_model,
    item.ai_description_metadata,
    item.use_ai_description,
    item.admin_notes,
    item.photo_count,
    item.first_photo_url,
    item.is_tax_ready,
    item.created_by,
    item.admin_url,
    item.agent_payload_url,
    item.ai_description_url,
    item.photos.map(toMaintenancePhoto),
    item.created_at,
    item.updated_at,
  );
}
