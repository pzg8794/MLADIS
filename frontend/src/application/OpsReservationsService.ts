import { OpsReservationsSnapshot } from '../domain/models';
import {
  filterReservations,
  OpsReservation,
  reservationOptions,
  reservationStatusCounts,
  type ReservationStatusFilter,
  type ReservationWorkspaceFilters,
} from '../domain/reservations';
import { OpsReservationsRepository } from '../infrastructure/OpsReservationsRepository';

export class OpsReservationsService {
  constructor(private readonly repository: OpsReservationsRepository) {}

  async loadReservations(): Promise<OpsReservationsSnapshot> {
    return this.repository.getSnapshot();
  }

  filterReservations(reservations: OpsReservation[], filters: ReservationWorkspaceFilters): OpsReservation[] {
    return filterReservations(reservations, filters);
  }

  reservationOptions(reservations: OpsReservation[]) {
    return reservationOptions(reservations);
  }

  statusCounts(reservations: OpsReservation[]): Record<ReservationStatusFilter, number> {
    return reservationStatusCounts(reservations);
  }

  async updateStatus(
    reservation: OpsReservation,
    status: 'reviewing' | 'confirmed' | 'cancelled',
  ): Promise<OpsReservation | null> {
    if (!reservation.canTransitionStatus()) {
      throw new Error('Only direct reservation requests can be updated from this workspace.');
    }
    return this.repository.updateStatus(reservation, status);
  }
}
