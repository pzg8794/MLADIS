import { SettingsRepository } from '../infrastructure/SettingsRepository';
import { HttpClient } from '../infrastructure/HttpClient';
import { ApiOpsWorkspaceRepository } from '../infrastructure/OpsWorkspaceRepository';
import { SettingsService } from './SettingsService';

export class SettingsFactory {
  static create(): SettingsService {
    const http = new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' });
    return new SettingsService(new SettingsRepository(new ApiOpsWorkspaceRepository(http)));
  }
}
