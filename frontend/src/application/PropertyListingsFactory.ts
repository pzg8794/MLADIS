import { PropertyListingsRepository } from '../infrastructure/PropertyListingsRepository';
import { PropertyListingsService } from './PropertyListingsService';

export class PropertyListingsFactory {
  static create(): PropertyListingsService {
    return new PropertyListingsService(new PropertyListingsRepository());
  }
}
