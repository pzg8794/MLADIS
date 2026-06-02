import {
  OpsAgentSnapshot,
  OpsCustomersSnapshot,
  OpsDepositsSnapshot,
  OpsReportsSnapshot,
} from '../domain/models';
import { OpsWorkspaceRepository } from '../infrastructure/OpsWorkspaceRepository';

export class OpsWorkspaceService {
  constructor(private readonly repository: OpsWorkspaceRepository) {}

  async loadReports(): Promise<OpsReportsSnapshot> {
    return this.repository.getReports();
  }

  async loadCustomers(): Promise<OpsCustomersSnapshot> {
    return this.repository.getCustomers();
  }

  async loadDeposits(): Promise<OpsDepositsSnapshot> {
    return this.repository.getDeposits();
  }

  async loadAgent(): Promise<OpsAgentSnapshot> {
    return this.repository.getAgent();
  }
}
