import { OpsReservationsSnapshot } from '../domain/models';
import { OpsReservationsRepository } from '../infrastructure/OpsReservationsRepository';

export class OpsReservationsService {
  constructor(private readonly repository: OpsReservationsRepository) {}

  async loadReservations(): Promise<OpsReservationsSnapshot> {
    return this.repository.getSnapshot();
  }
}
