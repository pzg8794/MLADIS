import {
  AgentQuestionSummary,
  CalendarAlert,
  DashboardMetric,
  DashboardSnapshot,
  DepositSummary,
  Money,
  ReservationSummary,
  StayPerformance,
} from '../domain/models';
import { HttpClient } from './HttpClient';

export interface DashboardRepository {
  getSnapshot(): Promise<DashboardSnapshot>;
}

interface ApiMetric {
  id: string;
  label: string;
  value: string;
  caption: string;
  trend?: 'up' | 'down' | 'neutral';
  trend_label?: string;
  accent?: DashboardMetric['accent'];
  progress?: number;
}

interface ApiReservation {
  id: number;
  guest_name: string;
  stay_name: string;
  check_in: string;
  check_out: string;
  guests: number;
  status: ReservationSummary['status'];
  admin_url: string;
  action_required?: boolean;
}

interface ApiDeposit {
  id: number;
  guest_name: string;
  stay_name: string;
  amount_cents: number;
  currency: string;
  provider: 'Stripe' | 'PayPal';
  status: DepositSummary['status'];
}

interface ApiAgentQuestion {
  id: number;
  topic: string;
  last_question: string;
  mode: AgentQuestionSummary['mode'];
  created_at: string;
}

interface ApiCalendarAlert {
  id: string;
  label: string;
  stay_name: string;
  date_range: string;
  severity?: CalendarAlert['severity'];
}

interface ApiStayPerformance {
  id: string;
  name: string;
  subtitle: string;
  image_url: string;
  rating: string;
  occupancy_label: string;
  revenue_label: string;
  detail_url: string;
  status?: StayPerformance['status'];
}

interface ApiDashboardSnapshot {
  metrics: ApiMetric[];
  reservations: ApiReservation[];
  deposits: ApiDeposit[];
  agent_questions: ApiAgentQuestion[];
  calendar_alerts: ApiCalendarAlert[];
  stays?: ApiStayPerformance[];
  generated_at: string;
}

export class ApiDashboardRepository implements DashboardRepository {
  constructor(private readonly http: HttpClient) {}

  async getSnapshot(): Promise<DashboardSnapshot> {
    const data = await this.http.get<ApiDashboardSnapshot>('/api/ops/summary/');
    return new DashboardSnapshot(
      data.metrics.map((item) => new DashboardMetric(item.id, item.label, item.value, item.caption, item.trend ?? 'neutral', item.trend_label ?? 'Stable', item.accent ?? 'teal', item.progress ?? 0)),
      data.reservations.map((item) => new ReservationSummary(item.id, item.guest_name, item.stay_name, item.check_in, item.check_out, item.guests, item.status, item.admin_url, item.action_required ?? false)),
      data.deposits.map((item) => new DepositSummary(item.id, item.guest_name, item.stay_name, new Money(item.amount_cents, item.currency), item.provider, item.status)),
      data.agent_questions.map((item) => new AgentQuestionSummary(item.id, item.topic, item.last_question, item.mode, item.created_at)),
      data.calendar_alerts.map((item) => new CalendarAlert(item.id, item.label, item.stay_name, item.date_range, item.severity ?? 'info')),
      (data.stays ?? []).map((item) => new StayPerformance(item.id, item.name, item.subtitle, item.image_url, item.rating, item.occupancy_label, item.revenue_label, item.detail_url, item.status ?? 'live')),
      data.generated_at,
      'api',
    );
  }
}
