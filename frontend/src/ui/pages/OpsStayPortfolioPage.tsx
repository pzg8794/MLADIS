import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Building2, CalendarDays, ExternalLink, MapPin, ShieldCheck } from 'lucide-react';
import { DashboardSnapshot } from '../../domain/models';
import { DashboardFactory } from '../../application/DashboardFactory';
import { StayPortfolio } from '../components/StayPortfolio';

export function OpsStayPortfolioPage() {
  const service = useMemo(() => DashboardFactory.create(), []);
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    service
      .loadDashboard()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load stay portfolio.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page ops-page--stays">
      <section className="ops-hero ops-hero--stays">
        <div>
          <span><Building2 size={16} /> Stay portfolio</span>
          <h2>Stay portfolio</h2>
          <p>Active MLADIS listings, occupancy posture, calendar readiness, and booking links in one focused view.</p>
        </div>
        <div className="ops-hero-actions">
          <a href="/ops/calendar/"><CalendarDays size={16} /> Calendar</a>
          <a href="/"><ExternalLink size={16} /> Live site</a>
        </div>
      </section>

      <section className="ops-metric-grid ops-stay-summary">
        <article>
          <span><MapPin size={14} /> Active stays</span>
          <strong>{snapshot.stays.length}</strong>
          <p>Santo Domingo Norte listings in the current portfolio.</p>
        </article>
        <article>
          <span><ShieldCheck size={14} /> Live feeds</span>
          <strong>{snapshot.stays.filter((stay) => stay.status === 'live').length}</strong>
          <p>Listings with calendar/feed readiness marked live.</p>
        </article>
        <article>
          <span>Needs review</span>
          <strong>{snapshot.stays.filter((stay) => stay.status !== 'live').length}</strong>
          <p>Listings that still need admin or calendar review.</p>
        </article>
      </section>

      <StayPortfolio stays={snapshot.stays} />
    </main>
  );
}
