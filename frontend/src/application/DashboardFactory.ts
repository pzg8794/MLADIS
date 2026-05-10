import { DashboardService } from './DashboardService';
import { ApiDashboardRepository, MockDashboardRepository } from '../infrastructure/DashboardRepository';
import { HttpClient } from '../infrastructure/HttpClient';

export class DashboardFactory {
  static create(): DashboardService {
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA !== 'false';

    if (useMockData) {
      return new DashboardService(new MockDashboardRepository());
    }

    return new DashboardService(
      new ApiDashboardRepository(
        new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' }),
      ),
    );
  }
}
