import type { CalendarWorkspace } from '../domain/calendar';
import type {
  CalendarBlockInput,
  CalendarPriceInput,
  CalendarWorkspaceQuery,
  CalendarWorkspaceRepository,
} from '../infrastructure/CalendarWorkspaceRepository';

export class CalendarWorkspaceService {
  constructor(private readonly repository: CalendarWorkspaceRepository) {}

  async loadWorkspace(query: CalendarWorkspaceQuery): Promise<CalendarWorkspace> {
    return this.repository.getWorkspace(query);
  }

  async createCalendarBlock(input: CalendarBlockInput): Promise<void> {
    return this.repository.createBlock(input);
  }

  async deleteCalendarBlock(id: number): Promise<void> {
    return this.repository.deleteBlock(id);
  }

  async createCalendarPrice(input: CalendarPriceInput): Promise<void> {
    return this.repository.createPrice(input);
  }

  async deleteCalendarPrice(id: number): Promise<void> {
    return this.repository.deletePrice(id);
  }
}
