import { Star } from 'lucide-react';
import { StayPerformance } from '../../domain/models';
import { StatusBadge } from './StatusBadge';

interface StayPortfolioProps {
  stays: StayPerformance[];
}

export function StayPortfolio({ stays }: StayPortfolioProps) {
  return (
    <section className="stay-portfolio" aria-labelledby="stay-portfolio-title">
      <div className="section-heading">
        <h2 id="stay-portfolio-title">Stay portfolio</h2>
        <p>Airbnb-sourced imagery with a cleaner operational layer for direct booking decisions.</p>
      </div>
      <div className="stay-grid">
        {stays.map((stay) => (
          <article className="stay-card" key={stay.id}>
            <img src={stay.imageUrl} alt={stay.name} loading="lazy" />
            <div className="stay-card__content">
              <div>
                <h3>{stay.name}</h3>
                <p>{stay.subtitle}</p>
              </div>
              <div className="stay-card__meta">
                <span><Star size={14} /> {stay.rating}</span>
                <span>{stay.occupancyLabel}</span>
                <strong>{stay.revenueLabel}</strong>
              </div>
              <StatusBadge label={stay.status === 'review' ? 'Needs review' : stay.status === 'blocked' ? 'Blocked' : 'Live'} tone={stay.status === 'review' ? 'warning' : stay.status === 'blocked' ? 'danger' : 'success'} />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
