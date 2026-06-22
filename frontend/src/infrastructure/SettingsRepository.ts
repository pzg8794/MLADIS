import { SettingsWorkspace } from '../domain/settings';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';
import type { OpsWorkspaceRepository } from './OpsWorkspaceRepository';

export class SettingsRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  async getWorkspace(): Promise<SettingsWorkspace> {
    try {
      return new SettingsWorkspace(await this.opsRepository.getSettings(), createWorkspaceMetadata('api'));
    } catch {
      return new SettingsWorkspace(null, createWorkspaceMetadata('fallback', ['settings API snapshot']));
    }
  }
}
