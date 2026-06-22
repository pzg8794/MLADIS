import type { SettingsWorkspace } from '../domain/settings';
import type { SettingsRepository } from '../infrastructure/SettingsRepository';

export class SettingsService {
  constructor(private readonly repository: SettingsRepository) {}

  async loadWorkspace(): Promise<SettingsWorkspace> {
    return this.repository.getWorkspace();
  }
}
