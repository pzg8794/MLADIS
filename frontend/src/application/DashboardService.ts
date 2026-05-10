import { DashboardSnapshot } from '../domain/models';
import { DashboardRepository } from '../infrastructure/DashboardRepository';

export class DashboardService {
  constructor(private readonly repository: DashboardRepository) {}

  async loadDashboard(): Promise<DashboardSnapshot> {
    return this.repository.getSnapshot();
  }
}
