import {
  AgentQuestionSummary,
  CalendarAlert,
  DashboardMetric,
  DashboardSnapshot,
  DepositSummary,
  Money,
  ReservationSummary,
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
}

interface ApiReservation {
  id: number;
  guest_name: string;
  stay_name: string;
  check_in: string;
  check_out: string;
  guests: number;
  status: ReservationSummary['status'];
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

interface ApiDashboardSnapshot {
  metrics: ApiMetric[];
  reservations: ApiReservation[];
  deposits: ApiDeposit[];
  agent_questions: ApiAgentQuestion[];
  calendar_alerts: ApiCalendarAlert[];
  generated_at: string;
}

export class ApiDashboardRepository implements DashboardRepository {
  constructor(private readonly http: HttpClient) {}

  async getSnapshot(): Promise<DashboardSnapshot> {
    const data = await this.http.get<ApiDashboardSnapshot>('/api/ops/summary/');
    return new DashboardSnapshot(
      data.metrics.map((item) => new DashboardMetric(item.id, item.label, item.value, item.caption, item.trend ?? 'neutral', item.trend_label ?? 'Stable')),
      data.reservations.map((item) => new ReservationSummary(item.id, item.guest_name, item.stay_name, item.check_in, item.check_out, item.guests, item.status, item.action_required ?? false)),
      data.deposits.map((item) => new DepositSummary(item.id, item.guest_name, item.stay_name, new Money(item.amount_cents, item.currency), item.provider, item.status)),
      data.agent_questions.map((item) => new AgentQuestionSummary(item.id, item.topic, item.last_question, item.mode, item.created_at)),
      data.calendar_alerts.map((item) => new CalendarAlert(item.id, item.label, item.stay_name, item.date_range, item.severity ?? 'info')),
      data.generated_at,
      'api',
    );
  }
}

export class MockDashboardRepository implements DashboardRepository {
  async getSnapshot(): Promise<DashboardSnapshot> {
    return new DashboardSnapshot(
      [
        new DashboardMetric('reservations', 'Reservations', '18', 'Open and upcoming requests', 'up', '+12% this month'),
        new DashboardMetric('deposits', 'Deposits', '$3.2k', 'Authorized or pending holds', 'up', '7 active holds'),
        new DashboardMetric('customers', 'Customers', '246', 'Guests and imported Airbnb contacts', 'up', '+31 imported'),
        new DashboardMetric('agent', 'Agent savings', '64%', 'Questions answered without OpenAI', 'up', 'FAQ layer active'),
      ],
      [
        new ReservationSummary(101, 'Maria R.', 'G-102 Tech Apartment', 'May 16', 'May 20', 4, 'reviewing', true),
        new ReservationSummary(102, 'Anthony B.', 'G-101 Comfort Stay', 'May 22', 'May 26', 2, 'confirmed'),
        new ReservationSummary(103, 'Family Group', '6-Bedroom Vacation Home', 'Jun 02', 'Jun 09', 10, 'new', true),
      ],
      [
        new DepositSummary(21, 'Maria R.', 'G-102 Tech Apartment', new Money(20000), 'Stripe', 'pending'),
        new DepositSummary(22, 'Anthony B.', 'G-101 Comfort Stay', new Money(20000), 'PayPal', 'authorized'),
      ],
      [
        new AgentQuestionSummary(1, 'deposit', 'How does the deposit work?', 'faq', 'Today'),
        new AgentQuestionSummary(2, 'availability', 'Can I book for next weekend?', 'openai', 'Today'),
        new AgentQuestionSummary(3, 'rules', 'Are parties allowed?', 'faq', 'Yesterday'),
      ],
      [
        new CalendarAlert('a1', 'Manual block needs review', 'G-102 Tech Apartment', 'May 18 - May 19', 'warning'),
        new CalendarAlert('a2', 'Price override active', '6-Bedroom Vacation Home', 'Jun 01 - Jun 15', 'info'),
      ],
      new Date().toISOString(),
      'mock',
    );
  }
}
