import { HttpClient } from '../infrastructure/HttpClient';
import { ApiPublicSiteRepository } from '../infrastructure/PublicSiteRepository';
import { PublicSiteService } from './PublicSiteService';

export class PublicSiteFactory {
  static create(): PublicSiteService {
    return new PublicSiteService(
      new ApiPublicSiteRepository(
        new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' }),
      ),
    );
  }
}
