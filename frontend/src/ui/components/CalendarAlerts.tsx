import { AlertCircle } from 'lucide-react';
import { CalendarAlert } from '../../domain/models';

interface CalendarAlertsProps {
  alerts: CalendarAlert[];
}

export function CalendarAlerts({ alerts }: CalendarAlertsProps) {
  return (
    <article className="dashboard-panel panel-large">
      <header className="panel-heading">
        <span className="panel-heading__icon"><AlertCircle size={19} /></span>
        <div>
          <h2>Calendar alerts</h2>
          <p>Blocks, overrides, and reminders that protect booking quality.</p>
        </div>
      </header>
      <div className="calendar-alerts">
        {alerts.map((alert) => (
          <div className={`calendar-alert calendar-alert--${alert.severity}`} key={alert.id}>
            <strong>{alert.label}</strong>
            <span>{alert.stayName}</span>
            <small>{alert.dateRange}</small>
          </div>
        ))}
      </div>
    </article>
  );
}
