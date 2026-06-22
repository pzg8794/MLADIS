import type { PropertyListingsWorkspace } from '../domain/properties';
import type { PropertyListingsRepository } from '../infrastructure/PropertyListingsRepository';

export class PropertyListingsService {
  constructor(private readonly repository: PropertyListingsRepository) {}

  loadWorkspace(): PropertyListingsWorkspace {
    return this.repository.getWorkspace();
  }
}
