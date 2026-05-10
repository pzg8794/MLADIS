import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import { DashboardMetric } from '../../domain/models';

interface MetricCardProps {
  metric: DashboardMetric;
}

export function MetricCard({ metric }: MetricCardProps) {
  const Icon = metric.trend === 'up' ? ArrowUpRight : metric.trend === 'down' ? ArrowDownRight : Minus;

  return (
    <article className="metric-card glass-card">
      <div>
        <p>{metric.label}</p>
        <strong>{metric.value}</strong>
      </div>
      <div className={`metric-card__trend metric-card__trend--${metric.trend}`}>
        <Icon size={18} />
        <span>{metric.trendLabel}</span>
      </div>
      <small>{metric.caption}</small>
    </article>
  );
}
