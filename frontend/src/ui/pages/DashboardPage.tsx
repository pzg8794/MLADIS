import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ArrowUpRight, MapPin, ShieldCheck } from 'lucide-react';
import { DashboardSnapshot } from '../../domain/models';
import { DashboardFactory } from '../../application/DashboardFactory';
import { MetricCard } from '../components/MetricCard';
import { DashboardSkeleton } from '../components/DashboardSkeleton';
import { ReservationBoard } from '../components/ReservationBoard';
import { DepositPanel } from '../components/DepositPanel';
import { AgentPanel } from '../components/AgentPanel';
import { CalendarAlerts } from '../components/CalendarAlerts';

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
    return <DashboardSkeleton />;
  }

  if (error || !snapshot) {
    return <section className="dashboard-error"><AlertCircle /> {error ?? 'No dashboard data available.'}</section>;
  }

  return (
    <main className="dashboard-content">
      <section className="command-hero">
        <div className="command-hero__copy">
          <span><MapPin size={16} /> Santo Domingo Norte operations</span>
          <h2>Operations cockpit</h2>
          <p>Live stay, deposit, guest, calendar, and agent activity in one place.</p>
          <div className="hero-actions">
            <a href="/ops/calendar/" aria-label="Open business calendar">
              Calendar
              <ArrowUpRight size={16} />
            </a>
            <a href="/ops/reports/" aria-label="Review reports">Reports</a>
          </div>
        </div>
        <div className="command-hero__panel" aria-label="Readiness summary">
          <div>
            <span>Availability confidence</span>
            <strong>92%</strong>
          </div>
          <div>
            <span>Deposit readiness</span>
            <strong>$200</strong>
          </div>
          <div>
            <span>Agent layer</span>
            <strong>FAQ + OpenAI</strong>
          </div>
        </div>
      </section>

      {snapshot.source === 'mock' && (
        <div className="mock-banner"><ShieldCheck size={17} /> Mock data is active. Set <code>VITE_USE_MOCK_DATA=false</code> when the live API is ready.</div>
      )}

      <section className="metric-grid">
        {snapshot.metrics.map((metric) => <MetricCard key={metric.id} metric={metric} />)}
      </section>

      <section className="dashboard-grid">
        <ReservationBoard reservations={snapshot.reservations} />
        <DepositPanel deposits={snapshot.deposits} />
        <AgentPanel questions={snapshot.agentQuestions} />
        <CalendarAlerts alerts={snapshot.calendarAlerts} />
      </section>
    </main>
  );
}
