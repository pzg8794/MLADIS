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

export class MockDashboardRepository implements DashboardRepository {
  async getSnapshot(): Promise<DashboardSnapshot> {
    return new DashboardSnapshot(
      [
        new DashboardMetric('reservations', 'Reservations', '18', 'Open and upcoming requests', 'up', '+12% this month', 'teal', 72),
        new DashboardMetric('deposits', 'Deposit holds', '$3.2k', 'Authorized or pending holds', 'up', '7 active holds', 'blue', 64),
        new DashboardMetric('customers', 'Guest CRM', '246', 'Guests and imported Airbnb contacts', 'up', '+31 imported', 'amber', 58),
        new DashboardMetric('agent', 'Agent coverage', '64%', 'Questions answered by the FAQ layer', 'up', 'FAQ layer active', 'violet', 64),
      ],
      [
        new ReservationSummary(101, 'Maria R.', 'G-102 Tech Apartment', 'May 16', 'May 20', 4, 'reviewing', '/admin/bookings/bookinginquiry/101/change/', true),
        new ReservationSummary(102, 'Anthony B.', 'G-101 Comfort Stay', 'May 22', 'May 26', 2, 'confirmed', '/admin/bookings/bookinginquiry/102/change/'),
        new ReservationSummary(103, 'Family Group', '6-Bedroom Vacation Home', 'Jun 02', 'Jun 09', 10, 'new', '/admin/bookings/bookinginquiry/103/change/', true),
        new ReservationSummary(104, 'Jessica L.', 'G-101 Comfort Stay', 'Jun 15', 'Jun 18', 3, 'confirmed', '/admin/bookings/bookinginquiry/104/change/'),
      ],
      [
        new DepositSummary(21, 'Maria R.', 'G-102 Tech Apartment', new Money(20000), 'Stripe', 'pending'),
        new DepositSummary(22, 'Anthony B.', 'G-101 Comfort Stay', new Money(20000), 'PayPal', 'authorized'),
        new DepositSummary(23, 'Family Group', '6-Bedroom Vacation Home', new Money(20000), 'Stripe', 'pending'),
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
      [
        new StayPerformance(
          'g101',
          'G-101 Comfort Stay',
          '3 bedrooms near Santo Domingo Norte',
          'https://a0.muscache.com/im/pictures/miso/Hosting-582161420407543691/original/c097c0de-d8eb-45da-be8a-644065f20ab8.jpeg?im_w=960&quality=80&auto=webp',
          '4.93',
          '82% occupied',
          '$4.8k this month',
          '/stays/g101/',
        ),
        new StayPerformance(
          'g102',
          'G-102 Tech Apartment',
          '3 bedrooms with pool access',
          'https://a0.muscache.com/im/pictures/miso/Hosting-587194328968598250/original/0c11621f-bae3-41b1-846f-c50f923b9bd8.jpeg?im_w=960&quality=80&auto=webp',
          '4.88',
          '76% occupied',
          '$4.1k this month',
          '/stays/g102/',
          'review',
        ),
        new StayPerformance(
          'six-bedroom',
          '6-Bedroom Vacation Home',
          'Large family stay with pool access',
          'https://a0.muscache.com/im/pictures/miso/Hosting-588632365342578374/original/6fe55920-ce15-4bbc-b560-3ecf159c192d.jpeg?im_w=960&quality=80&auto=webp',
          '4.69',
          '68% occupied',
          '$6.7k this month',
          '/stays/six-bedroom/',
        ),
      ],
      new Date().toISOString(),
      'mock',
    );
  }
}
