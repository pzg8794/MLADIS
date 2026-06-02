import { ApiOpsWorkspaceRepository } from '../infrastructure/OpsWorkspaceRepository';
import { HttpClient } from '../infrastructure/HttpClient';
import { OpsWorkspaceService } from './OpsWorkspaceService';

export class OpsWorkspaceFactory {
  static create(): OpsWorkspaceService {
    return new OpsWorkspaceService(
      new ApiOpsWorkspaceRepository(
        new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' }),
      ),
    );
  }
}
