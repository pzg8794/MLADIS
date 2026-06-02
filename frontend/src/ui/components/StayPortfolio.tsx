import { CircleDollarSign, Percent, Star } from 'lucide-react';
import { StayPerformance } from '../../domain/models';
import { StatusBadge, type BadgeTone } from './StatusBadge';

interface StayPortfolioProps {
  stays: StayPerformance[];
}

function toneForStatus(status: StayPerformance['status']): BadgeTone {
  if (status === 'live') return 'success';
  if (status === 'review') return 'warning';
  return 'danger';
}

function labelForStatus(status: StayPerformance['status']) {
  if (status === 'live') return 'Live';
  if (status === 'review') return 'Needs review';
  return 'Blocked';
}

export function StayPortfolio({ stays }: StayPortfolioProps) {
  return (
    <section className="stay-portfolio" aria-label="Stay portfolio overview">
      <header className="section-heading">
        <div>
          <h2>Stay portfolio</h2>
          <p>Compare occupancy, revenue posture, and review health across the active MLADIS listings.</p>
        </div>
      </header>
      <div className="stay-grid">
        {stays.map((stay) => (
          <article className="dashboard-panel stay-card" key={stay.id}>
            <img src={stay.imageUrl} alt={stay.name} />
            <div className="stay-card__content">
              <div>
                <h3>{stay.name}</h3>
                <p>{stay.subtitle}</p>
              </div>
              <div className="stay-card__meta">
                <span><Star size={15} /> {stay.rating}</span>
                <span><Percent size={15} /> {stay.occupancyLabel}</span>
                <strong><CircleDollarSign size={15} /> {stay.revenueLabel}</strong>
              </div>
              <StatusBadge label={labelForStatus(stay.status)} tone={toneForStatus(stay.status)} />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}