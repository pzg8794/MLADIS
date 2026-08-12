import { DashboardService } from './DashboardService';
import { ApiDashboardRepository } from '../infrastructure/DashboardRepository';
import { HttpClient } from '../infrastructure/HttpClient';

export class DashboardFactory {
  static create(): DashboardService {
    return new DashboardService(
      new ApiDashboardRepository(
        new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' }),
      ),
    );
  }
}
