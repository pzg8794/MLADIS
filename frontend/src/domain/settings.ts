import type { OpsSettingsSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export class SettingsWorkspace {
  constructor(
    public readonly snapshot: OpsSettingsSnapshot | null,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}

  get source() {
    return this.metadata.source;
  }
}
