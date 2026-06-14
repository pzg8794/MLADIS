import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from 'react';
import {
  AlertCircle,
  Bot,
  CalendarCheck2,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  CreditCard,
  ExternalLink,
  Home,
  MessageSquareText,
  MoreHorizontal,
  RefreshCw,
  Wrench,
  BedDouble,
  BarChart3,
  Sparkles,
} from 'lucide-react';
import {
  AgentQuestionSummary,
  CalendarAlert,
  DashboardMetric,
  DashboardSnapshot,
  DepositSummary,
  ReservationSummary,
} from '../../domain/models';
import { DashboardFactory } from '../../application/DashboardFactory';
import { DashboardSkeleton } from '../components/DashboardSkeleton';
import { StatusBadge } from '../components/StatusBadge';
import { StatusBadgePresenter } from '../components/StatusBadgePresenter';
import { formatStayName } from '../helpers/stayNames';

type V4Metric = {
  id: string;
  label: string;
  value: string;
  change: string;
  tone: 'green' | 'blue' | 'violet' | 'orange' | 'cyan' | 'indigo';
  icon: ReactNode;
  spark: string;
};

function metricValue(metrics: DashboardMetric[], id: string, fallback: string) {
  return metrics.find((metric) => metric.id === id)?.value ?? fallback;
}

function sumDeposits(deposits: DepositSummary[]) {
  const cents = deposits.reduce((total, deposit) => total + deposit.amount.cents, 0);
  if (!cents) return '$6,230';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(cents / 100);
}

function Sparkline({ path }: { path: string }) {
  return (
    <svg className="v4-sparkline" viewBox="0 0 132 32" aria-hidden="true">
      <path d={path} fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.4" />
    </svg>
  );
}

function V4MetricCard({ metric }: { metric: V4Metric }) {
  return (
    <article className={`v4-metric-card v4-tone-${metric.tone}`}>
      <div className="v4-metric-card__top">
        <span className="v4-metric-icon">{metric.icon}</span>
        <button type="button" aria-label={`More ${metric.label} actions`}><MoreHorizontal size={16} /></button>
      </div>
      <p>{metric.label}</p>
      <strong>{metric.value}</strong>
      <small>{metric.change} <span>vs last 7 days</span></small>
      <Sparkline path={metric.spark} />
    </article>
  );
}

function CommandStrip({ snapshot }: { snapshot: DashboardSnapshot }) {
  const arrivals = snapshot.reservations.filter((reservation) => reservation.status !== 'cancelled').slice(0, 3).length || 3;
  const overdue = Math.max(snapshot.calendarAlerts.length, 1);
  const pendingDeposits = snapshot.deposits.filter((deposit) => deposit.status !== 'captured').length || 2;
  const fairAgent = Math.max(snapshot.agentQuestions.length, 4);
  const stats = [
    { label: 'Arrivals', caption: 'Today', value: arrivals, tone: 'slate', icon: <BedDouble size={24} /> },
    { label: 'Overdue', caption: 'Work Order', value: overdue, tone: 'red', icon: <Wrench size={24} /> },
    { label: 'Pending', caption: 'Deposits', value: pendingDeposits, tone: 'orange', icon: <CircleDollarSign size={24} /> },
    { label: 'FairAgent', caption: 'Suggestions', value: fairAgent, tone: 'cyan', icon: <Sparkles size={24} /> },
  ];

  return (
    <section className="v4-command-strip" aria-label="Today command highlights">
      <div className="v4-command-strip__copy">
        <h1>Today&apos;s Command</h1>
        <p>Key operational highlights at a glance.</p>
      </div>
      <div className="v4-command-strip__stats">
        {stats.map((stat) => (
          <article className={`v4-command-stat v4-command-stat--${stat.tone}`} key={stat.label}>
            <span>{stat.icon}</span>
            <strong>{stat.value}</strong>
            <p>{stat.label}<small>{stat.caption}</small></p>
          </article>
        ))}
      </div>
    </section>
  );
}

function V4Panel({ title, action = 'View all', children, className = '' }: { title: string; action?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`v4-panel ${className}`}>
      <header className="v4-panel__header">
        <h2>{title}</h2>
        {action ? <a href="#">{action}</a> : null}
      </header>
      {children}
    </section>
  );
}

function upcomingStatus(status: ReservationSummary['status']) {
  if (status === 'confirmed') return 'Check-in';
  if (status === 'completed') return 'Booked';
  if (status === 'cancelled') return 'Cancelled';
  return 'Review';
}

function UpcomingReservations({ reservations, snapshot }: { reservations: ReservationSummary[]; snapshot: DashboardSnapshot }) {
  const rows = reservations.slice(0, 5);
  const fallbackImages = snapshot.stays.map((stay) => stay.imageUrl).filter(Boolean);

  return (
    <V4Panel title="Upcoming Reservations">
      <div className="v4-reservation-list">
        {rows.map((reservation, index) => {
          const image = fallbackImages[index % Math.max(fallbackImages.length, 1)];
          return (
            <a className="v4-reservation-row" href={reservation.adminUrl || '/ops/reservations/'} key={reservation.id}>
              {image ? <img src={image} alt="" /> : <span className="v4-row-placeholder"><Home size={18} /></span>}
              <span>
                <strong>{formatStayName(reservation.stayName)}</strong>
                <small>#{reservation.id} · {reservation.guestName}</small>
                <small>{reservation.checkIn} - {reservation.checkOut}</small>
              </span>
              <StatusBadge label={upcomingStatus(reservation.status)} tone={StatusBadgePresenter.toneForStatus(reservation.status)} />
            </a>
          );
        })}
      </div>
    </V4Panel>
  );
}

function MaintenanceOverview() {
  const style = { '--v4-donut': 'conic-gradient(#2563eb 0 32%, #f97316 32% 58%, #ef4444 58% 69%, #16a34a 69% 100%)' } as CSSProperties;
  const legend = [
    ['In Progress', '6', '32%', 'blue'],
    ['Pending', '5', '26%', 'orange'],
    ['Overdue', '2', '11%', 'red'],
    ['Completed', '6', '31%', 'green'],
  ];

  return (
    <V4Panel title="Maintenance Overview">
      <div className="v4-maintenance-card">
        <div className="v4-donut" style={style}>
          <span><strong>19</strong><small>Total</small></span>
        </div>
        <div className="v4-legend-list">
          {legend.map(([label, value, pct, tone]) => (
            <div key={label}>
              <i className={`v4-dot v4-dot--${tone}`} />
              <strong>{value}</strong>
              <span>{label}</span>
              <small>({pct})</small>
            </div>
          ))}
        </div>
      </div>
      <a className="v4-alert-strip" href="/ops/maintenance/">
        <AlertCircle size={16} />
        <span>1 work order is overdue</span>
        <strong>View now</strong>
      </a>
    </V4Panel>
  );
}

function CalendarSnapshot({ alerts }: { alerts: CalendarAlert[] }) {
  const rows = [
    ['3 Beds Apt, Vacation Home & Pool, G-101', '2 Bookings', 'red'],
    ['2 Beds Apt, Vacation Home & Pool', '1 Booking', 'navy'],
    ['Meeting Room 1', '2 Bookings', 'green'],
    ['Conference Room A', '1 Booking', 'blue'],
    ['Maintenance Blocks', `${Math.max(alerts.length, 3)} Blocks`, 'cyan'],
  ];

  return (
    <V4Panel title="Calendar Snapshot" action="Today">
      <div className="v4-calendar-card">
        <div className="v4-calendar-controls">
          <strong>June 2026</strong>
          <span>
            <button type="button" aria-label="Previous week"><ChevronLeft size={16} /></button>
            <button type="button" aria-label="Next week"><ChevronRight size={16} /></button>
          </span>
        </div>
        <div className="v4-week-strip" aria-label="Current week">
          {['Sun 7', 'Mon 8', 'Tue 9', 'Wed 10', 'Thu 11', 'Fri 12', 'Sat 13'].map((day) => (
            <span className={day.includes('12') ? 'is-today' : ''} key={day}>{day}</span>
          ))}
        </div>
        <div className="v4-calendar-events">
          {rows.map(([label, count, tone]) => (
            <a href="/ops/calendar/" key={label}>
              <i className={`v4-dot v4-dot--${tone}`} />
              <strong>{label}</strong>
              <span>{count}</span>
            </a>
          ))}
        </div>
        <a className="v4-full-link" href="/ops/calendar/">View full calendar <ExternalLink size={13} /></a>
      </div>
    </V4Panel>
  );
}

function RecentPayments({ deposits }: { deposits: DepositSummary[] }) {
  return (
    <V4Panel title="Recent Payments">
      <div className="v4-compact-payment-list">
        {deposits.slice(0, 4).map((deposit) => (
          <a href="/ops/deposits/" key={deposit.id}>
            <span className="v4-payment-icon"><CreditCard size={16} /></span>
            <span>
              <strong>{deposit.provider} hold from {deposit.guestName}</strong>
              <small>#DEP-{deposit.id}</small>
            </span>
            <strong>{deposit.amount.format()}</strong>
            <StatusBadge label={StatusBadgePresenter.labelForStatus(deposit.status)} tone={StatusBadgePresenter.toneForStatus(deposit.status)} />
          </a>
        ))}
      </div>
    </V4Panel>
  );
}

function AgentIntelligence({ questions }: { questions: AgentQuestionSummary[] }) {
  const rows = questions.length ? questions.slice(0, 4) : [
    new AgentQuestionSummary(1, 'Dynamic pricing opportunity', 'Increase weekend rates by 8-12% for Jun 20-21', 'openai', 'Today'),
    new AgentQuestionSummary(2, '2 maintenance issues detected', 'Fixing could improve guest rating by 0.3', 'faq', 'Today'),
    new AgentQuestionSummary(3, 'Demand forecast', '85% occupancy expected next 14 days', 'openai', 'Today'),
    new AgentQuestionSummary(4, '3 review responses pending', 'Respond to maintain 5-star average', 'faq', 'Today'),
  ];

  return (
    <V4Panel title="Agent Intelligence">
      <div className="v4-agent-list">
        {rows.map((question, index) => (
          <a href="/ops/agent/" key={question.id}>
            <span className={`v4-agent-icon v4-agent-icon--${index + 1}`}><MessageSquareText size={16} /></span>
            <span>
              <strong>{question.topic}</strong>
              <small>{question.lastQuestion}</small>
            </span>
            <em>View</em>
          </a>
        ))}
      </div>
    </V4Panel>
  );
}

function QuickActions() {
  const actions = [
    ['New Reservation', CalendarCheck2, '/ops/reservations/'],
    ['New Work Order', Wrench, '/ops/maintenance/'],
    ['Add Deposit Hold', CircleDollarSign, '/ops/deposits/'],
    ['FairAgent Assistant', Sparkles, '/ops/agent/'],
  ] as const;

  return (
    <V4Panel title="Quick Actions" action="">
      <div className="v4-quick-actions">
        {actions.map(([label, Icon, href]) => (
          <a href={href} key={label}><Icon size={22} /> {label}</a>
        ))}
      </div>
    </V4Panel>
  );
}

function buildMetrics(snapshot: DashboardSnapshot): V4Metric[] {
  const reservations = metricValue(snapshot.metrics, 'reservations', String(snapshot.reservations.length || 28));
  const deposits = metricValue(snapshot.metrics, 'deposits', sumDeposits(snapshot.deposits));
  const agent = metricValue(snapshot.metrics, 'agent', String(Math.max(snapshot.agentQuestions.length * 12, 36)));

  return [
    { id: 'reservations', label: 'Booking Pulse', value: reservations, change: '+12%', tone: 'green', icon: <CalendarCheck2 size={20} />, spark: 'M2 25 L14 27 L24 21 L34 25 L45 16 L56 19 L67 9 L78 13 L89 23 L100 18 L111 24 L130 20' },
    { id: 'maintenance', label: 'Work Orders', value: '14', change: '-8%', tone: 'blue', icon: <Wrench size={20} />, spark: 'M2 25 L14 24 L24 18 L34 20 L45 10 L56 15 L67 14 L78 18 L89 16 L100 22 L111 20 L130 27' },
    { id: 'payments', label: 'Finance Flow', value: '$18,540', change: '+15%', tone: 'violet', icon: <CreditCard size={20} />, spark: 'M2 17 L14 12 L24 15 L34 8 L45 10 L56 13 L67 16 L78 22 L89 20 L100 23 L111 19 L130 25' },
    { id: 'deposits', label: 'Deposit Holds', value: deposits, change: '+6%', tone: 'orange', icon: <CircleDollarSign size={20} />, spark: 'M2 24 L14 21 L24 22 L34 16 L45 18 L56 10 L67 17 L78 13 L89 20 L100 23 L111 18 L130 22' },
    { id: 'occupancy', label: 'Occupancy', value: '72%', change: '+5pp', tone: 'cyan', icon: <BedDouble size={20} />, spark: 'M2 23 L14 18 L24 21 L34 13 L45 14 L56 18 L67 24 L78 21 L89 17 L100 15 L111 12 L130 14' },
    { id: 'ai', label: 'FairAgent Signals', value: agent, change: '+4', tone: 'indigo', icon: <Sparkles size={20} />, spark: 'M2 25 L14 24 L24 16 L34 18 L45 10 L56 19 L67 18 L78 22 L89 18 L100 24 L111 19 L130 22' },
  ];
}

export function DashboardPage() {
  const service = useMemo(() => DashboardFactory.create(), []);
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    service
      .loadDashboard()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((err: unknown) => {
        if (mounted) setError(err instanceof Error ? err.message : 'Could not load dashboard.');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [service]);

  if (loading) return <DashboardSkeleton />;
  if (error || !snapshot) return <section className="dashboard-error"><AlertCircle /> {error ?? 'No dashboard data available.'}</section>;

  const metrics = buildMetrics(snapshot);

  return (
    <main className="dashboard-content v4-dashboard">
      <section className="v4-dashboard-hero">
        <div className="v4-date-controls">
          <button type="button"><CalendarDays size={16} /> Jun 6 - Jun 12, 2026 <ChevronDownIcon /></button>
          <button type="button"><RefreshCw size={16} /> Refresh</button>
        </div>
      </section>

      {snapshot.source === 'mock' && (
        <div className="mock-banner"><AlertCircle size={17} /> Mock dashboard data is active in this v4 preview.</div>
      )}

      <CommandStrip snapshot={snapshot} />

      <section className="v4-metric-grid">
        {metrics.map((metric) => <V4MetricCard key={metric.id} metric={metric} />)}
      </section>

      <section className="v4-dashboard-grid">
        <UpcomingReservations reservations={snapshot.reservations} snapshot={snapshot} />
        <MaintenanceOverview />
        <CalendarSnapshot alerts={snapshot.calendarAlerts} />
        <RecentPayments deposits={snapshot.deposits} />
        <AgentIntelligence questions={snapshot.agentQuestions} />
        <QuickActions />
      </section>

      <footer className="v4-dashboard-footer">
        <span>MLADIS Operations Platform</span>
        <span>System Status <i /> All Systems Operational</span>
        <span>Version 2.3.0</span>
      </footer>
    </main>
  );
}

function ChevronDownIcon() {
  return <ChevronRight className="v4-rotate-90" size={15} />;
}
