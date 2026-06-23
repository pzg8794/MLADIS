import { HttpClient } from '../infrastructure/HttpClient';
import { GuestRepository } from '../infrastructure/GuestRepository';
import { GuestService } from './GuestService';

export class GuestFactory {
  static create(): GuestService {
    return new GuestService(
      new GuestRepository(new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' })),
    );
  }
}
