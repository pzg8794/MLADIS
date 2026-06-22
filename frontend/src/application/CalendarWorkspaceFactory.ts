import { CalendarWorkspaceRepository } from '../infrastructure/CalendarWorkspaceRepository';
import { HttpClient } from '../infrastructure/HttpClient';
import { ApiOpsWorkspaceRepository } from '../infrastructure/OpsWorkspaceRepository';
import { CalendarWorkspaceService } from './CalendarWorkspaceService';

export class CalendarWorkspaceFactory {
  static create(): CalendarWorkspaceService {
    const http = new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' });
    return new CalendarWorkspaceService(
      new CalendarWorkspaceRepository(new ApiOpsWorkspaceRepository(http)),
    );
  }
}
