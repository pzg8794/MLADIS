import { CalendarWorkspace } from '../domain/calendar';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';
import type {
  OpsCalendarBlockInput,
  OpsCalendarPriceInput,
  OpsCalendarQuery,
  OpsWorkspaceRepository,
} from './OpsWorkspaceRepository';

export type CalendarWorkspaceQuery = OpsCalendarQuery;
export type CalendarBlockInput = OpsCalendarBlockInput;
export type CalendarPriceInput = OpsCalendarPriceInput;

export class CalendarWorkspaceRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  async getWorkspace(query: CalendarWorkspaceQuery): Promise<CalendarWorkspace> {
    const snapshot = await this.opsRepository.getCalendar(query);
    return new CalendarWorkspace(snapshot, createWorkspaceMetadata('api'));
  }

  async createBlock(input: CalendarBlockInput): Promise<void> {
    return this.opsRepository.createCalendarBlock(input);
  }

  async deleteBlock(id: number): Promise<void> {
    return this.opsRepository.deleteCalendarBlock(id);
  }

  async createPrice(input: CalendarPriceInput): Promise<void> {
    return this.opsRepository.createCalendarPrice(input);
  }

  async deletePrice(id: number): Promise<void> {
    return this.opsRepository.deleteCalendarPrice(id);
  }
}
