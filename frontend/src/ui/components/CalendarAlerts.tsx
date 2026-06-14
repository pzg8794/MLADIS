import { AlertCircle, ArrowUpRight, ChevronRight } from 'lucide-react';
import { CalendarAlert } from '../../domain/models';
import { formatStayName } from '../helpers/stayNames';

interface CalendarAlertsProps {
  alerts: CalendarAlert[];
}

export function CalendarAlerts({ alerts }: CalendarAlertsProps) {
  return (
    <details className="dashboard-panel panel-large dashboard-collapse-card">
      <summary className="panel-heading dashboard-panel-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <span className="panel-heading__icon"><AlertCircle size={19} /></span>
        <div>
          <h2>Calendar work queue</h2>
          <p>Active blocks, price overrides, and feed setup warnings.</p>
        </div>
        <a className="panel-action-link" href="/ops/calendar/" onClick={(event) => event.stopPropagation()}>
          Open calendar <ArrowUpRight size={14} />
        </a>
      </summary>
      <div className="calendar-alerts">
        {alerts.map((alert) => (
          <div className={`calendar-alert calendar-alert--${alert.severity}`} key={alert.id}>
            <strong>{alert.label}</strong>
            <span>{formatStayName(alert.stayName)}</span>
            <small>{alert.dateRange}</small>
          </div>
        ))}
      </div>
    </details>
  );
}
