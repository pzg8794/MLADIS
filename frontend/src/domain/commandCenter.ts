import type { DashboardSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export class CommandCenterSnapshot {
  constructor(
    public readonly dashboard: DashboardSnapshot,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata(
      dashboard.source === 'api' ? 'api' : 'fallback',
      dashboard.source === 'api' ? [] : ['command center API snapshot'],
    ),
  ) {}
}
