import { AdminWorkspaceRepository } from '../infrastructure/AdminWorkspaceRepository';
import { HttpClient } from '../infrastructure/HttpClient';
import { ApiOpsWorkspaceRepository } from '../infrastructure/OpsWorkspaceRepository';
import { AdminWorkspaceService } from './AdminWorkspaceService';

export class AdminWorkspaceFactory {
  static create(): AdminWorkspaceService {
    const http = new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' });
    return new AdminWorkspaceService(new AdminWorkspaceRepository(new ApiOpsWorkspaceRepository(http)));
  }
}
