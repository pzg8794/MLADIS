import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  AlertCircle,
  Bot,
  CalendarDays,
  CircleDollarSign,
  ClipboardCheck,
  CreditCard,
  Home,
  RefreshCw,
  Users,
  Wrench,
} from 'lucide-react';
import {
  DashboardMetric,
  DashboardSnapshot,
  DepositSummary,
  ReservationSummary,
  StayPerformance,
} from '../../domain/models';
import { DashboardFactory } from '../../application/DashboardFactory';
import { DashboardSkeleton } from '../components/DashboardSkeleton';
import { StatusBadge } from '../components/StatusBadge';
import { StatusBadgePresenter } from '../components/StatusBadgePresenter';
import { formatStayName } from '../helpers/stayNames';

function WorkspacePanel({ title, href, linkLabel, children, className = '' }: {
  title: string;
  href: string;
  linkLabel: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`ops-command-panel ${className}`}>
      <header><h2>{title}</h2><a href={href}>{linkLabel}</a></header>
      {children}
    </section>
  );
}

function MetricCard({ metric }: { metric: DashboardMetric }) {
  return (
    <article className={`ops-command-metric ops-command-metric--${metric.accent}`}>
      <span aria-hidden="true" />
      <div><p>{metric.label}</p><strong>{metric.value}</strong><small>{metric.caption}</small></div>
      <em className={`is-${metric.trend}`}>{metric.trendLabel}</em>
    </article>
  );
}

function reservationLabel(reservation: ReservationSummary) {
  if (reservation.status === 'confirmed') return 'Confirmed';
  if (reservation.status === 'completed') return 'Completed';
  if (reservation.status === 'cancelled') return 'Cancelled';
  return reservation.actionRequired ? 'Review needed' : 'New';
}

function ReservationsPanel({ reservations, stays }: { reservations: ReservationSummary[]; stays: StayPerformance[] }) {
  const images = new Map(stays.map((stay) => [stay.name.toLowerCase(), stay.imageUrl]));
  return (
    <WorkspacePanel title="Reservation queue" href="/ops/reservations/" linkLabel="Open reservations">
      <div className="ops-command-records">
        {reservations.length ? reservations.slice(0, 6).map((reservation) => {
          const image = images.get(reservation.stayName.toLowerCase()) || stays[0]?.imageUrl;
          return (
            <a href={`/ops/reservations/?reservation=${reservation.id}`} key={reservation.id}>
              {image ? <img src={image} alt="" /> : <i><Home size={17} /></i>}
              <span><strong>{formatStayName(reservation.stayName)}</strong><small>{reservation.guestName} · {reservation.checkIn} - {reservation.checkOut}</small></span>
              <StatusBadge label={reservationLabel(reservation)} tone={StatusBadgePresenter.toneForStatus(reservation.status)} />
            </a>
          );
        }) : <p className="ops-command-empty">No reservation records need attention.</p>}
      </div>
    </WorkspacePanel>
  );
}

function DepositsPanel({ deposits }: { deposits: DepositSummary[] }) {
  return (
    <WorkspacePanel title="Recent deposit activity" href="/ops/deposits/" linkLabel="Open deposits">
      <div className="ops-command-records ops-command-records--compact">
        {deposits.length ? deposits.slice(0, 6).map((deposit) => (
          <a href="/ops/deposits/" key={deposit.id}>
            <i><CircleDollarSign size={17} /></i>
            <span><strong>{deposit.guestName}</strong><small>{formatStayName(deposit.stayName)} · {deposit.provider}</small></span>
            <b>{deposit.amount.format()}</b>
            <StatusBadge label={StatusBadgePresenter.labelForStatus(deposit.status)} tone={StatusBadgePresenter.toneForStatus(deposit.status)} />
          </a>
        )) : <p className="ops-command-empty">No deposit records are available.</p>}
      </div>
    </WorkspacePanel>
  );
}

function PropertiesPanel({ stays }: { stays: StayPerformance[] }) {
  return (
    <WorkspacePanel title="Property performance" href="/ops/properties/" linkLabel="Open properties">
      <div className="ops-command-properties">
        {stays.length ? stays.map((stay) => (
          <a href={`/ops/properties/?stay=${encodeURIComponent(stay.id)}`} key={stay.id}>
            {stay.imageUrl ? <img src={stay.imageUrl} alt="" /> : <i><Home size={18} /></i>}
            <span><strong>{formatStayName(stay.name)}</strong><small>★ {stay.rating} · {stay.occupancyLabel} · {stay.revenueLabel}</small></span>
          </a>
        )) : <p className="ops-command-empty">No published properties are available.</p>}
      </div>
    </WorkspacePanel>
  );
}

function AlertsPanel({ snapshot }: { snapshot: DashboardSnapshot }) {
  return (
    <WorkspacePanel title="Operational alerts" href="/ops/calendar/" linkLabel="Open calendar">
      <div className="ops-command-alerts">
        {snapshot.calendarAlerts.length ? snapshot.calendarAlerts.map((alert) => (
          <a className={`is-${alert.severity}`} href="/ops/calendar/" key={alert.id}>
            <AlertCircle size={16} />
            <span><strong>{alert.label}</strong><small>{formatStayName(alert.stayName)} · {alert.dateRange}</small></span>
          </a>
        )) : <p className="ops-command-empty">No calendar alerts are active.</p>}
      </div>
    </WorkspacePanel>
  );
}

const workspaceLinks = [
  { label: 'Reservations', caption: 'Review and manage guest requests', href: '/ops/reservations/', icon: ClipboardCheck },
  { label: 'Guests', caption: 'Open real guest profiles', href: '/ops/guests/', icon: Users },
  { label: 'Properties', caption: 'Manage live stay listings', href: '/ops/properties/', icon: Home },
  { label: 'Payments', caption: 'Review payment transactions', href: '/ops/payments/', icon: CreditCard },
  { label: 'Deposits', caption: 'Manage authorization holds', href: '/ops/deposits/', icon: CircleDollarSign },
  { label: 'Maintenance', caption: 'Open the maintenance ledger', href: '/ops/maintenance/', icon: Wrench },
  { label: 'Calendar', caption: 'Availability and reservation dates', href: '/ops/calendar/', icon: CalendarDays },
  { label: 'FairAgent', caption: 'Questions and knowledge coverage', href: '/ops/agent/', icon: Bot },
] as const;

export function DashboardPage() {
  const service = useMemo(() => DashboardFactory.create(), []);
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setSnapshot(await service.loadDashboard()); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not load the Command Center.'); }
    finally { setLoading(false); }
  }, [service]);

  useEffect(() => { void load(); }, [load]);

  if (loading && !snapshot) return <DashboardSkeleton />;
  if (error || !snapshot) {
    return <section className="dashboard-error"><AlertCircle /><span>{error ?? 'No operational data is available.'}</span><button type="button" onClick={() => void load()}>Try again</button></section>;
  }

  const generatedAt = new Date(snapshot.generatedAt);
  const generatedLabel = Number.isNaN(generatedAt.getTime()) ? 'Live database snapshot' : `Updated ${generatedAt.toLocaleString()}`;

  return (
    <main className="dashboard-content ops-command-center">
      <header className="ops-command-header">
        <div><span>Live operations</span><h1>Command Center</h1><p>Real reservation, guest, deposit, property, and calendar records in one workspace.</p></div>
        <button type="button" onClick={() => void load()} disabled={loading}><RefreshCw size={16} className={loading ? 'is-spinning' : ''} /> Refresh</button>
      </header>

      <section className="ops-command-metrics" aria-label="Live operational metrics">
        {snapshot.metrics.map((metric) => <MetricCard key={metric.id} metric={metric} />)}
      </section>

      <section className="ops-command-layout">
        <ReservationsPanel reservations={snapshot.reservations} stays={snapshot.stays} />
        <DepositsPanel deposits={snapshot.deposits} />
        <PropertiesPanel stays={snapshot.stays} />
        <AlertsPanel snapshot={snapshot} />
      </section>

      <section className="ops-command-workspaces" aria-label="Operations workspaces">
        <header><h2>Operations hub</h2><span>Every action opens a live system workspace.</span></header>
        <div>{workspaceLinks.map(({ label, caption, href, icon: Icon }) => (
          <a href={href} key={label}><i><Icon size={18} /></i><span><strong>{label}</strong><small>{caption}</small></span></a>
        ))}</div>
      </section>

      <footer className="ops-command-footer"><span><i /> Live database records</span><span>{generatedLabel}</span></footer>
    </main>
  );
}
