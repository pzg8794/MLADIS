import type { ReportWorkspace } from '../domain/reports';
import type { ReportsRepository } from '../infrastructure/ReportsRepository';

export class ReportsService {
  constructor(private readonly repository: ReportsRepository) {}

  fallbackWorkspace(): ReportWorkspace {
    return this.repository.fallback();
  }

  async loadWorkspace(): Promise<ReportWorkspace> {
    return this.repository.getWorkspace();
  }
}
