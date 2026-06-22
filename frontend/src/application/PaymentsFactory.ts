import { HttpClient } from '../infrastructure/HttpClient';
import { PaymentsRepository } from '../infrastructure/PaymentsRepository';
import { PaymentsService } from './PaymentsService';

export class PaymentsFactory {
  static create(): PaymentsService {
    return new PaymentsService(
      new PaymentsRepository(new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' })),
    );
  }
}
