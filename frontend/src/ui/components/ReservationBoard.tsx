import { useMemo, useState } from 'react';
import { ArrowRight, CalendarCheck2, ChevronRight } from 'lucide-react';
import { ReservationSummary } from '../../domain/models';
import { StatusBadge } from './StatusBadge';
import { StatusBadgePresenter } from './StatusBadgePresenter';
import { formatStayName } from '../helpers/stayNames';

interface ReservationBoardProps {
  reservations: ReservationSummary[];
}

type ReservationFilter = 'all' | 'attention' | 'confirmed';

export function ReservationBoard({ reservations }: ReservationBoardProps) {
  const [filter, setFilter] = useState<ReservationFilter>('all');
  const filteredReservations = useMemo(() => reservations.filter((reservation) => {
    if (filter === 'attention') return reservation.actionRequired;
    if (filter === 'confirmed') return reservation.status === 'confirmed';
    return true;
  }), [filter, reservations]);

  return (
    <details className="dashboard-panel panel-large reservation-board dashboard-collapse-card" data-testid="reservation-board">
      <summary className="panel-heading dashboard-panel-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <span className="panel-heading__icon"><CalendarCheck2 size={19} /></span>
        <div>
          <h2>Reservation command center</h2>
          <p>Latest booking requests. Arrows open the protected reservation record.</p>
        </div>
        <div className="segmented-control" aria-label="Reservation filter" onClick={(event) => event.stopPropagation()}>
          {[
            ['all', 'All'],
            ['attention', 'Needs review'],
            ['confirmed', 'Confirmed'],
          ].map(([value, label]) => (
            <button className={filter === value ? 'active' : ''} key={value} onClick={() => setFilter(value as ReservationFilter)} type="button">
              {label}
            </button>
          ))}
        </div>
      </summary>
      <div className="reservation-list">
        {filteredReservations.map((reservation) => (
          <div className={reservation.actionRequired ? 'reservation-row is-priority' : 'reservation-row'} key={reservation.id}>
            <div>
              <strong>{reservation.guestName}</strong>
              <span>{formatStayName(reservation.stayName)}</span>
            </div>
            <div>
              <strong>{reservation.checkIn} - {reservation.checkOut}</strong>
              <span>{reservation.guests} guests</span>
            </div>
            <StatusBadge label={StatusBadgePresenter.labelForStatus(reservation.status)} tone={StatusBadgePresenter.toneForStatus(reservation.status)} />
            <a className="icon-button" href={reservation.adminUrl || '/ops/reservations/'} aria-label={`Review ${reservation.guestName}`}>
              <ArrowRight size={17} />
            </a>
          </div>
        ))}
      </div>
    </details>
  );
}
