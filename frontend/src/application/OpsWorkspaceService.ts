import {
  OpsAgentSnapshot,
  OpsAdminSnapshot,
  OpsCalendarSnapshot,
  OpsCustomersSnapshot,
  OpsDepositsSnapshot,
  OpsMaintenanceEvent,
  OpsMaintenanceSnapshot,
  OpsReportsSnapshot,
  OpsSettingsSnapshot,
  OpsWorkboardSnapshot,
  OpsWorkItem,
} from '../domain/models';
import {
  OpsCalendarBlockInput,
  OpsCalendarPriceInput,
  OpsCalendarQuery,
  OpsMaintenanceDraftAiDescriptionResult,
  OpsWorkspaceRepository,
} from '../infrastructure/OpsWorkspaceRepository';

export class OpsWorkspaceService {
  constructor(private readonly repository: OpsWorkspaceRepository) {}

  async loadWorkboard(): Promise<OpsWorkboardSnapshot> {
    return this.repository.getWorkboard();
  }

  async setWorkItemCompletion(id: number, completed: boolean): Promise<OpsWorkItem> {
    return this.repository.setWorkItemCompletion(id, completed);
  }

  async loadReports(): Promise<OpsReportsSnapshot> {
    return this.repository.getReports();
  }

  async loadAdmin(): Promise<OpsAdminSnapshot> {
    return this.repository.getAdmin();
  }

  async loadSettings(): Promise<OpsSettingsSnapshot> {
    return this.repository.getSettings();
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

  async loadMaintenance(): Promise<OpsMaintenanceSnapshot> {
    return this.repository.getMaintenance();
  }

  async createMaintenanceEvent(input: FormData): Promise<OpsMaintenanceEvent> {
    return this.repository.createMaintenanceEvent(input);
  }

  async loadMaintenanceAgentPayload(id: string): Promise<Record<string, unknown>> {
    return this.repository.getMaintenanceAgentPayload(id);
  }

  async generateMaintenanceAiDescription(id: string): Promise<OpsMaintenanceEvent> {
    return this.repository.generateMaintenanceAiDescription(id);
  }

  async generateMaintenanceDraftAiDescription(input: FormData): Promise<OpsMaintenanceDraftAiDescriptionResult> {
    return this.repository.generateMaintenanceDraftAiDescription(input);
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
