import { PublicSiteRepository } from '../infrastructure/PublicSiteRepository';

export class PublicSiteService {
  constructor(private readonly repository: PublicSiteRepository) {}

  async loadSite() {
    return this.repository.getSnapshot();
  }
}
