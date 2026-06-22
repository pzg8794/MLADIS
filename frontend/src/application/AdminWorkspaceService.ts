import type { AdminWorkspace } from '../domain/admin';
import type { AdminWorkspaceRepository } from '../infrastructure/AdminWorkspaceRepository';

export class AdminWorkspaceService {
  constructor(private readonly repository: AdminWorkspaceRepository) {}

  fallbackWorkspace(): AdminWorkspace {
    return this.repository.fallback();
  }

  async loadWorkspace(): Promise<AdminWorkspace> {
    return this.repository.getWorkspace();
  }
}
