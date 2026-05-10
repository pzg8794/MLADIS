import type { CSSProperties } from 'react';
import { ArrowDownRight, ArrowUpRight, Bot, CalendarCheck2, CreditCard, Minus, Users } from 'lucide-react';
import { DashboardMetric } from '../../domain/models';

interface MetricCardProps {
  metric: DashboardMetric;
}

export function MetricCard({ metric }: MetricCardProps) {
  const TrendIcon = metric.trend === 'up' ? ArrowUpRight : metric.trend === 'down' ? ArrowDownRight : Minus;
  const metricIcons = {
    reservations: CalendarCheck2,
    deposits: CreditCard,
    customers: Users,
    agent: Bot,
  };
  const Icon = metricIcons[metric.id as keyof typeof metricIcons] ?? CalendarCheck2;
  const progressStyle = { '--metric-progress': `${Math.max(0, Math.min(100, metric.progress))}%` } as CSSProperties;

  return (
    <article className={`metric-card metric-card--${metric.accent}`} style={progressStyle}>
      <div className="metric-card__topline">
        <span className="metric-card__icon"><Icon size={20} /></span>
        <div className={`metric-card__trend metric-card__trend--${metric.trend}`}>
          <TrendIcon size={16} />
          <span>{metric.trendLabel}</span>
        </div>
      </div>
      <div>
        <p>{metric.label}</p>
        <strong>{metric.value}</strong>
      </div>
      <div className="metric-card__meter" aria-hidden="true"><span /></div>
      <small>{metric.caption}</small>
    </article>
  );
}
