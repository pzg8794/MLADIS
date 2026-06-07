import {
  OpsAgentSnapshot,
  OpsCalendarSnapshot,
  OpsCustomersSnapshot,
  OpsDepositsSnapshot,
  OpsReportsSnapshot,
} from '../domain/models';
import {
  OpsCalendarBlockInput,
  OpsCalendarPriceInput,
  OpsCalendarQuery,
  OpsWorkspaceRepository,
} from '../infrastructure/OpsWorkspaceRepository';

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

  async loadCalendar(query: OpsCalendarQuery): Promise<OpsCalendarSnapshot> {
    return this.repository.getCalendar(query);
  }

  async createCalendarBlock(input: OpsCalendarBlockInput): Promise<void> {
    return this.repository.createCalendarBlock(input);
  }

  async deleteCalendarBlock(id: number): Promise<void> {
    return this.repository.deleteCalendarBlock(id);
  }

  async createCalendarPrice(input: OpsCalendarPriceInput): Promise<void> {
    return this.repository.createCalendarPrice(input);
  }

  async deleteCalendarPrice(id: number): Promise<void> {
    return this.repository.deleteCalendarPrice(id);
  }
}
