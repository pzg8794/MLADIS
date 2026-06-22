import type { OpsCalendarSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export class CalendarWorkspace {
  constructor(
    public readonly snapshot: OpsCalendarSnapshot,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}
}
