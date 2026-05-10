import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Bot, CalendarCheck, CreditCard, RefreshCw } from 'lucide-react';
import { DashboardSnapshot } from '../../domain/models';
import { DashboardFactory } from '../../application/DashboardFactory';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge, StatusBadgePresenter } from '../components/StatusBadge';

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

  if (loading) {
    return <section className="dashboard-loading glass-card"><RefreshCw className="spin" /> Loading MLADIS dashboard...</section>;
  }

  if (error || !snapshot) {
    return <section className="dashboard-error glass-card"><AlertCircle /> {error ?? 'No dashboard data available.'}</section>;
  }

  return (
    <main className="dashboard-content">
      {snapshot.source === 'mock' && (
        <div className="mock-banner glass-card">Mock data mode is active. Wire <code>/api/ops/summary/</code> and set <code>VITE_USE_MOCK_DATA=false</code> when ready.</div>
      )}

      <section className="metric-grid">
        {snapshot.metrics.map((metric) => <MetricCard key={metric.id} metric={metric} />)}
      </section>

      <section className="dashboard-grid">
        <article className="dashboard-panel glass-card panel-large">
          <header><CalendarCheck /><div><h2>Reservations requiring attention</h2><p>Admin-confirmed bookings and upcoming stays.</p></div></header>
          <div className="reservation-list">
            {snapshot.reservations.map((reservation) => (
              <div className="reservation-row" key={reservation.id}>
                <div><strong>{reservation.guestName}</strong><span>{reservation.stayName}</span></div>
                <div><strong>{reservation.checkIn} - {reservation.checkOut}</strong><span>{reservation.guests} guests</span></div>
                <StatusBadge label={StatusBadgePresenter.labelForStatus(reservation.status)} tone={StatusBadgePresenter.toneForStatus(reservation.status)} />
              </div>
            ))}
          </div>
        </article>

        <article className="dashboard-panel glass-card">
          <header><CreditCard /><div><h2>Deposit holds</h2><p>Stripe and PayPal authorization status.</p></div></header>
          <div className="compact-list">
            {snapshot.deposits.map((deposit) => (
              <div key={deposit.id}>
                <span><strong>{deposit.guestName}</strong><small>{deposit.provider} · {deposit.stayName}</small></span>
                <span><strong>{deposit.amount.format()}</strong><StatusBadge label={StatusBadgePresenter.labelForStatus(deposit.status)} tone={StatusBadgePresenter.toneForStatus(deposit.status)} /></span>
              </div>
            ))}
          </div>
        </article>

        <article className="dashboard-panel glass-card">
          <header><Bot /><div><h2>Agent intelligence</h2><p>FAQ vs OpenAI usage signals.</p></div></header>
          <div className="compact-list">
            {snapshot.agentQuestions.map((question) => (
              <div key={question.id}>
                <span><strong>{question.topic}</strong><small>{question.lastQuestion}</small></span>
                <StatusBadge label={StatusBadgePresenter.labelForStatus(question.mode)} tone={StatusBadgePresenter.toneForStatus(question.mode)} />
              </div>
            ))}
          </div>
        </article>

        <article className="dashboard-panel glass-card panel-large">
          <header><AlertCircle /><div><h2>Calendar alerts</h2><p>Blocks, overrides, and operational reminders.</p></div></header>
          <div className="calendar-alerts">
            {snapshot.calendarAlerts.map((alert) => (
              <div className={`calendar-alert calendar-alert--${alert.severity}`} key={alert.id}>
                <strong>{alert.label}</strong>
                <span>{alert.stayName}</span>
                <small>{alert.dateRange}</small>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
