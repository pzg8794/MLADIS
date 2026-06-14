import { ApiOpsReservationsRepository } from '../infrastructure/OpsReservationsRepository';
import { HttpClient } from '../infrastructure/HttpClient';
import { OpsReservationsService } from './OpsReservationsService';

export class OpsReservationsFactory {
  static create(): OpsReservationsService {
    return new OpsReservationsService(
      new ApiOpsReservationsRepository(
        new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' }),
      ),
    );
  }
}
