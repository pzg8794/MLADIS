import { useMemo, useState } from 'react';
import { ArrowRight, CalendarCheck2 } from 'lucide-react';
import { ReservationSummary } from '../../domain/models';
import { StatusBadge } from './StatusBadge';
import { StatusBadgePresenter } from './StatusBadgePresenter';

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
    <article className="dashboard-panel panel-large reservation-board" data-testid="reservation-board">
      <header className="panel-heading">
        <span className="panel-heading__icon"><CalendarCheck2 size={19} /></span>
        <div>
          <h2>Reservation command center</h2>
          <p>Prioritize guest requests, calendar confidence, and upcoming arrivals.</p>
        </div>
        <div className="segmented-control" aria-label="Reservation filter">
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
      </header>
      <div className="reservation-list">
        {filteredReservations.map((reservation) => (
          <div className={reservation.actionRequired ? 'reservation-row is-priority' : 'reservation-row'} key={reservation.id}>
            <div>
              <strong>{reservation.guestName}</strong>
              <span>{reservation.stayName}</span>
            </div>
            <div>
              <strong>{reservation.checkIn} - {reservation.checkOut}</strong>
              <span>{reservation.guests} guests</span>
            </div>
            <StatusBadge label={StatusBadgePresenter.labelForStatus(reservation.status)} tone={StatusBadgePresenter.toneForStatus(reservation.status)} />
            <button className="icon-button" type="button" aria-label={`Review ${reservation.guestName}`}>
              <ArrowRight size={17} />
            </button>
          </div>
        ))}
      </div>
    </article>
  );
}
