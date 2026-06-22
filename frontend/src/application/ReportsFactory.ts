import { HttpClient } from '../infrastructure/HttpClient';
import { ApiOpsWorkspaceRepository } from '../infrastructure/OpsWorkspaceRepository';
import { ReportsRepository } from '../infrastructure/ReportsRepository';
import { ReportsService } from './ReportsService';

export class ReportsFactory {
  static create(): ReportsService {
    const http = new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' });
    return new ReportsService(new ReportsRepository(new ApiOpsWorkspaceRepository(http)));
  }
}
